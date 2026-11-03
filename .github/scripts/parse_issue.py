import re
import pandas as pd
from collections import defaultdict
from request_utils import get_record, check_uri
from parse_metadata_utils import parse_publication, parse_software, parse_organization
from parse_utils import parse_name_or_orcid, parse_yes_no_choice, get_authors, get_funders, process_funding_data, parse_image_and_caption, validate_slug, extract_doi_parts, extract_orcid, remove_duplicates, parse_size, identify_separator, separate_string
from dateutil import parser
from datetime import datetime

def read_issue_body(issue_body):
    """
    Parses the markdown content of a GitHub issue body and extracts structured data.

    This function uses regular expressions to identify markdown headings (formatted as '### Heading') and the text that follows them up to the next heading or the end of the document. It constructs a dictionary where each heading is a key and the associated text is the corresponding value.

    Parameters:
    - issue_body (str): The markdown content of a GitHub issue body.

    Returns:
    - dict: A dictionary with keys derived from markdown headings and values containing the text following these headings up to the next heading or the end of the document.

    Note:
    - The function assumes that the issue body uses '###' markdown syntax for headings.
    - Headings are used as dictionary keys and should be unique within the issue body for the resulting dictionary to capture all data correctly.
    """
    regex = r"### *(?P<key>.*?)\s*[\r\n]+(?P<value>[\s\S]*?)(?=###|$)"
    data = dict(re.findall(regex, issue_body))

    # GitHub wraps textarea values configured with `render: text` in a fenced
    # code block.  The fence is presentation markup, not part of the user's
    # response, and must not be passed to author, URI, or list parsers.
    for key, value in data.items():
        lines = value.strip().splitlines()
        if len(lines) >= 2 and lines[0].strip().startswith("```") and lines[-1].strip() == "```":
            data[key] = "\n".join(lines[1:-1]).strip()
    return data


def null_response_check(string):
    """
    This function evaluates whether the input string is either explicitly marked as "_No response_"
    or is an empty string. It is designed to trigger certain prefill actions or defaults in applications
    where user inputs can be explicitly stated as no response or left blank.

    Parameters:
    string (str): The input string to be checked for a null or empty response.

    Returns:
    bool: True if the input string is "_No response_" or an empty string, indicating a null response.
          False otherwise.
    """
    result = False
    if string == "_No response_" or string == "":
        result = True
    return result


def parse_issue(issue):

    """
    Parses issue data to extract and structure relevant information into a dictionary format suitable for metadata representation.

    The function processes the body of an issue, extracting information based on predefined headings. It applies mappings, validations, and transformations to structure this information according to Research Object Crate (RO-Crate) metadata standards and other specified requirements. It also generates an error log capturing issues encountered during the parsing process, such as missing responses, invalid data, or errors in fetching related metadata.

    Parameters:
    - issue (object): An object representing the GitHub issue, containing at least a 'body' attribute with the issue's content.

    Processing Steps:
    1. Extract key-value pairs from the issue body using regular expressions, where keys are derived from headings and values from the subsequent text.
    2. Initialize an empty data dictionary to hold structured metadata and an error log string.
    3. For each expected piece of information (e.g., creator, slug, license), perform the following:
       - Extract and clean the relevant data from the extracted key-value pairs.
       - Validate and transform the data as necessary (e.g., checking validity of slugs, parsing DOIs, loading license information from a CSV).
       - Update the data dictionary with the structured information.
       - Log any warnings or errors encountered during processing in the error log.
    4. Return the structured metadata dictionary along with the error log.

    Returns:
    - tuple: A tuple containing two elements:
        - data_dict (dict): A dictionary containing structured metadata extracted and processed from the issue.
        - msg_log (str): A string containing logged warnings and errors encountered during the parsing process.

    Note:
    - The function assumes the presence of external helper functions for specific processing steps, such as `parse_name_or_orcid`, `validate_slug`, `load_entity_template`, `recursively_filter_key`, `load_crate_template`, `dict_to_ro_crate_mapping`, `customise_ro_crate`, `flatten_crate`, `parse_publication`, `get_record`, `get_authors`, `get_funders`, `check_uri`, `parse_software`, `parse_image_and_caption`, which need to be defined elsewhere.
    - The function also relies on external resources, such as a CSV file for license information, and assumes a specific structure for the issue body based on headings and responses.
    - In general, the function steps are not order dependent. However, to work correctlly some order dependence is required. For instance, the publication record must be created before it can be used to prefil other sections.
    - For this reason, parts of the record (publication, software) that may be used in creating other items, get built first.
    """

    #read in the issue markdown as a dictionary
    data = read_issue_body(issue.body)


    msg_log = ""


    data_dict = {}

    #############
    # Fill in 'publication' record first as it may be required by other items
    #############

    # associated publication DOI
    publication_doi = data["publication DOI"].strip()
    publication_record = {}

    if publication_doi == "_No response_":
        msg_log += "**Associated Publication**\n"
        msg_log += "Warning: No DOI provided. \n"
    else:
        try:
            publication_metadata, log1 = get_record("publication", publication_doi)
            publication_record, log2 = parse_publication(publication_metadata)
            if log1 or log2:
                msg_log += "**Associated Publication**\n" + log1 + log2
        except Exception as err:
            msg_log += "**Associated Publication**\n"
            msg_log += f"Warning: unable to obtain metadata for DOI `{publication_doi}` \n"
            msg_log += f"`{err}`\n"

    data_dict["publication"] = publication_record

    #############
    # Fill in 'software' record next as it may be required by other items
    #############
    # software framework DOI/URI
    software_doi = data["software DOI/URI"].strip()

    software_doi_only = extract_doi_parts(software_doi)

    software_record={"@type": "SoftwareApplication"}

    if software_doi == "_No response_":
        msg_log += "**Software Framework DOI/URI**\n"
        msg_log += "Warning: no DOI/URI provided.\n"

    else:
        try:
            software_metadata, log1 = get_record("software", software_doi_only)
            software_record, log2 = parse_software(software_metadata, software_doi)
            if log1 or log2:
                msg_log += "**Software Framework DOI/URI**\n" + log1 + log2
        except Exception as err:
            msg_log += "**Software Framework DOI/URI**\n"
            msg_log += f"Warning: unable to obtain metadata for DOI `{software_doi}` \n"
            msg_log += f"`{err}`\n"
    #else:
            #msg_log += "**Software Framework DOI/URI**\n Non-Zenodo software dois not yet supported\n"

    # software framework source repository
    software_repo = data["Software source repository"].strip()

    if software_repo == "_No response_":
        msg_log += "**Software Repository**\n"
        msg_log += "Warning: no repository URL provided. \n"
    else:
        response = check_uri(software_repo)
        if response == "OK":
            software_record["codeRepository"] = software_repo
        else:
            msg_log += "**Software Repository**\n" + response + "\n"

    # name of primary software framework
    software_name = data["Provide the name of the software (e.g. Underworld, ASPECT, Badlands, OpenFOAM)"].strip()

    if software_name == "_No response_":
        try:
            software_name = software_record['name']
        except:
            msg_log += "**Name of primary software framework**\n"
            msg_log += "Warning: no name found \n"
    else:
        software_record["name"] = software_name     # N.B. this will overwrite any name obtained from the DOI

    # software framework authors
    authors = data['software authors'].strip().split('\r\n')

    #if authors[0] == "_No response_":
    if null_response_check(authors[0]):
        try:
            software_author_list = software_record["author"]
        except:
            software_author_list = []
            msg_log += "**Software framework authors**\n"
            msg_log += "Warning: no authors found \n"
    else:
        software_author_list, log = get_authors(authors)
        software_record["author"] = software_author_list     # N.B. this will overwrite any name obtained from the DOI
        if log:
            msg_log += "**Software framework authors**\n" + log

    # software & algorithm keywords
    #software_keywords = [x.strip() for x in data["software & algorithm keywords"].split(",")]
    software_keywords = separate_string(data["software & algorithm keywords"])

    #if software_keywords[0] == "_No response_":
    if null_response_check(software_keywords[0]):
        msg_log += "**Software & algorithm keywords**\n"
        msg_log += "Warning: no keywords given. \n"
    else:
        software_record["keywords"] = software_keywords

    # Software version used (tag, version, or commit SHA supplied by the
    # submitter).  Keep this separate from softwareVersion obtained from a
    # DOI so that an explicitly supplied value takes precedence.
    software_version = data["Software version used."].strip()
    if not null_response_check(software_version):
        software_record["softwareVersion"] = software_version

    data_dict["software"] = software_record


    #############
    # Section 1
    #############
    # The following fields get added to the data_dict: submitter, creator, contributor, data_creator.

    # submitter (individual). Not necessarily the creator of the original model.
    submitter = data["submitter ORCID (or name)"].strip()
    submitter_record, log = parse_name_or_orcid(submitter)
    data_dict["submitter"] = submitter_record
    if log:
        msg_log += "**Submitter**\n" + log +"\n"

    # model creators
    creators = data['contributing authors'].strip().split('\r\n')
    #test if the input has an orcid type, and if so, make sure only the orcid id is present


    #first check for null response, and try to use publication record
    if null_response_check(creators[0]):
        try:
            creators_list = publication_record["author"]
        except:
            creators_list = []
            msg_log += "**Model creators**\n"
            msg_log += "Warning: no creators found \n"

    #now if we got returned a response, try to parse it
    else:
        for index, item in enumerate(creators):
            orcid_id = extract_orcid(item )
            if orcid_id:
                creators[index] = orcid_id

        creators_list, log = get_authors(creators)
        if log:
            msg_log += "**Model creators**\n" + log

    data_dict["creators"] = creators_list


    # model contributors. This has been depricated. Now we simply record Creators, and submitter.
    #contributors = data['contributing authors'].strip().split('\r\n')
    #test if the input has an orcid type, and if so, make sure only the orcid id is present
    #orcid_id = extract_orcid(contributors[0])
    #if orcid_id:
    #    contributors = [extract_orcid(p) for p in contributors]
    #if contributors[0] == "_No response_":
    #    try:
    #        contributors_list = publication_record["author"]
    #    except:
    #        contributors_list = []
    #        msg_log += "**Model contributors**\n"
    #        msg_log += "Warning: no contributors found \n"
    #else:
    #    contributors_list, log = get_authors(contributors)
    #    if log:
    #        msg_log += "**Model contributors**\n" + log
    #data_dict["contributors"] = contributors_list

    #now apply some logic? to the list of people involved...
    #remove any creators from contributors list so these do not intersect (currently only uses @id to match)
    #data_dict['contributors'] = remove_duplicates(data_dict['creators'], data_dict['contributors'])

    #check if the submitter is either a creator of contributor.
    #If not, make them a contrinbutor.
    #result = remove_duplicates(data_dict['contributors'], (remove_duplicates(data_dict['creators'], [data_dict['submitter']] )))
    #if result:
    #    data_dict['contributors'] = result


    # slug
    proposed_slug = data["slug"].strip()
    data_dict["proposed_slug"] = proposed_slug

    slug, log = validate_slug(proposed_slug)
    data_dict["slug"] = slug
    if log:
        msg_log += "**Model Repository Slug**\n" + log + '\n'

    # FoR codes
    about_record = {
        "@id": "https://linked.data.gov.au/def/anzsrc-for/2020/370401",
        "@type": "DefinedTerm",
        "name": "Computational modelling and simulation in earth sciences",
        "termCode": "370401"
        }

    data_dict["for_codes"] = about_record

    # license
    license = data["license"].strip()

    def find_file_upwards( fName: str, maxLevels: int=5) -> str | None:
        """
        Search function to find file `fName` by relative path. 
        Works by searching up a directory a maximum number of `maxLevels` from the cwd.
        """
        import os
        
        tmp = fName
        for _ in range(maxLevels):
            if os.path.exists( tmp ):
                return tmp
            else:
                # go up one directory
                tmp = '../' + tmp

        raise RuntimeError(f"Couldn't find {fName}")

    lfile = find_file_upwards('.github/resources/licenses.csv')
    try:
        license_lut = pd.read_csv(lfile, dtype=str)
    except:
        raise RuntimeError("Can't read license file")
    #e.g. https://www.researchobject.org/ro-crate/1.1/contextual-entities.html#licensing-access-control-and-copyright
    #license,name,url,text,website_path
    license_record={"@type": "CreativeWork"}
    if license != "alternative":
        license_record["@id"] = license_lut[license_lut.license == license].url.values[0]
        license_record["description"] = license_lut[license_lut.license == license].name.values[0]
        license_record["website_path"] = license_lut[license_lut.license == license].website_path.values[0]
        license_record["url"] = license_lut[license_lut.license == license].text.values[0]
        license_record["name"] = license_lut[license_lut.license == license].license.values[0]
    else:
        license_record["name"] = "alternative"
    data_dict["license"] = license_record

    # model category
    #model_category = [x.strip() for x in data["model category"].split(",")]
    model_category = separate_string(data["model category"])

    #if model_category[0] == "_No response_":
    if null_response_check(model_category[0]):
        model_category = []
        msg_log += "**Model category**\n"
        msg_log += "Warning: No category selected \n"

    data_dict["model_category"] = model_category


    # model status
    model_status = []
    try:
        #model_status = [x.strip() for x in data["model status"].split(",")]
        model_status = separate_string(data["model status"])

        #if model_status[0] == "_No response_":
        if null_response_check(model_status[0]):
            msg_log += "**Model status**\n"
            msg_log += "Warning: No model status selected \n"
    except:
        msg_log += "Warning: No model status enrty found \n"
    data_dict["model_status"] = model_status


    # title
    title = data["title"].strip()

    #if title == "_No response_":
    if null_response_check(title):
        try:
            title = publication_record['name']
        except:
            title = ""
            msg_log += "**Title**\n"
            msg_log += "Warning: no title found \n"

    data_dict["title"] = title

    # abstract
    abstract = data["abstract"].strip()

    #if abstract == "_No response_":
    if null_response_check(abstract):
        try:
            abstract = publication_record['abstract']
        except:
            abstract = ""
            msg_log += "**abstract**\n"
            msg_log += "Warning: no abstract entered, nor abstract for associated publication \n"

    data_dict["abstract"] = abstract

    # description - brief plain langauge summary.
    description = data["description"].strip()
    data_dict["description"] = description

    # scientific keywords
    #keywords = [x.strip() for x in data["scientific keywords"].split(",")]
    keywords = separate_string(data["scientific keywords"])

    #if keywords[0] == "_No response_":
    if null_response_check(keywords[0]):
        keywords = []
        msg_log += "**Scientific keywords**\n"
        msg_log += "Warning: No keywords given \n"

    data_dict["scientific_keywords"] = keywords

    # funder
    #funders = [x.strip() for x in data["funder"].split(",")]

    funders_string = data["funder"]
    funders_dict = process_funding_data(funders_string)

    #if funders[0] == "_No response_":
    #if null_response_check(funders[0]):
    #    try:
    #        funder_list = publication_record['funder']
    #    except:
    #        funder_list = []
    #        msg_log += "**Funder**\n"
    #        msg_log += "Warning: No funders provided or found in publication. \n"
    #else:
    #    funder_list, log = get_funders(funders)
    #    if log:
    #        msg_log += "**Funder**\n" + log
    #
    data_dict["funder"] = funders_dict['funders']
    data_dict["funding"] = funders_dict['funding']

    #############
    # Section 2
    #############

    # embargo, record as a Tuple with a Boolean, and a date
    model_embargo = (False, datetime.min.strftime('%Y-%m-%d'))
    try:
        embargo = data["model embargo?"].strip()
        #if model_embargo[0] == "_No response_":
        if null_response_check(embargo):
            pass
        else:
            try:
                date_input = parser.parse(embargo )
                #calling the dateutil parser simply provides the error checking.
                #leading/trailing whitespaces are okay, and get removed.
                model_embargo = (True, date_input.strftime('%Y-%m-%d') )
            except:
                msg_log += "Warning: Could not parse Embargo date. Check format.\n"
    except:
        msg_log += "Warning: No model embargo entry found \n"

    data_dict["embargo"] = model_embargo






    # include model code
    model_code = data["include model inputs?"].strip()
    data_dict["include_model_code"] = parse_yes_no_choice(model_code)

    # model links.  The prototype form intentionally uses one field for
    # existing input/output repositories and DOIs, rather than separate code
    # and output DOI fields.  Preserve all links on the model-input entity;
    # the old single DOI slot is left empty because multiple links cannot be
    # represented reliably as one identifier.
    model_code_record = {}
    model_links = separate_string(data["model links"])
    if null_response_check(model_links[0]):
        model_links = []
        msg_log += "**Model links**\n"
        msg_log += "Warning: No model links provided. \n"
    model_code_record["doi"] = ""
    model_code_record["links"] = model_links

    # model code/inputs notes
    model_code_notes = data["model input usage, a.k.a reproducibility"].strip()

    #if model_code_notes == "_No response_":
    if null_response_check(model_code_notes):
        model_code_notes = ""
        msg_log += "**Model code/inputs notes**\n"
        msg_log += "Warning: No notes provided.\n"

    model_code_record["notes"] = model_code_notes

    data_dict["model_code_inputs"] = model_code_record



    # include model output data
    model_output = data["include model output?"].strip()
    #having this outside the record
    #anticipates that we might choose not to build the record if False
    data_dict["include_model_output"] = parse_yes_no_choice(model_output)



    # model output data
    model_output_record = {}

    # The prototype form no longer asks for separate data creators.  Use the
    # contributing/model creators for output provenance, matching the old
    # parser's fallback behavior when that field was blank.
    data_creators_list = data_dict["creators"]
    model_output_record["creators"] = data_creators_list



    # The prototype form has no separate output DOI field; any shared model
    # links were retained on model_code_inputs.links above.
    model_output_record["doi"] = ""

    # model output notes
    model_output_notes = data["model output notes"].strip()

    #if model_output_notes == "_No response_":
    if null_response_check(model_output_notes):
        model_output_notes = ""
        msg_log += "**Model data notes**\n"
        msg_log += "Warning: No notes provided.\n"

    model_output_record["notes"] = model_output_notes

    # model output size
    model_output_size = data["model output size"].strip()
    data_bytes_value = None

    #if model_output_size == "_No response_":
    if null_response_check(model_output_size):
            model_output_size = ""
            msg_log += "**Model data size**\n"
            msg_log += "Warning: No notes provided.\n"

    if model_output_size:
        data_bytes_value, size_msg_log = parse_size(model_output_size)
    else:
        data_bytes_value, size_msg_log = None, ""

    if size_msg_log:
        msg_log +=size_msg_log

    model_output_record["size"] = data_bytes_value

    data_dict["model_output_data"] = model_output_record


    #############
    # Section 3
    #############


    # computer URI/DOI
    #need to check the logic of the log messages here.

    computer_record = {}
    log1 = ''
    computer_uri = data["computer URI/DOI"].strip()
    #if computer_uri == "_No response_":
    if null_response_check(computer_uri):
        msg_log += "**Computer URI/DOI**\n"
        msg_log += "Warning: No URI/DOI provided. \n"
    else:
        response = check_uri(computer_uri)

        if response == "OK":
            #data_dict["computer_uri"] = computer_uri
            #if we have some kind of valid URI, we'll try to build a record
            computer_record.update({'@type': 'Service'})
            computer_record.update({'name': ''})
            computer_record.update({'url': computer_uri})
            computer_record.update({'@id': computer_uri})
            try:
                #check for RoR
                if "ror.org" in computer_uri:
                    record, get_log = get_record("organization", computer_uri)
                    compute_org_record, parse_log = parse_organization(record)
                    if get_log or parse_log:
                        log1 += get_log + parse_log
                    computer_record.update({'name': compute_org_record['name']})
                #check for valid DOI
                elif extract_doi_parts(computer_uri) != 'No valid DOI found in the input string.':
                    computer_record, log1 = get_record('software', computer_uri)

            except:
                pass
        else:
            msg_log += "**Computer URI/DOI**\n" + response + log1 + "\n"

            #except:
            #msg_log += "**Computer URI/DOI**\n" + "there was a problem parsing Computer URI/DOI" + log1 + "\n"


    data_dict["computer_resource"] = computer_record

    #############
    # Section 4
    #############
    # landing page image and caption
    img_string = data["add landing page image"].strip()
    empty_image_record = {"filename": None, "url": ""}

    #if img_string == "_No response_":
    if null_response_check(img_string):
        msg_log += "**Landing page image**\n"
        msg_log += "Warning: No image uploaded.\n\n"
        data_dict["landing_image"] = empty_image_record
    else:
        landing_image_record, log = parse_image_and_caption(img_string, "landing_image")
        if log:
            msg_log += "**Landing page image**\n" + log + "\n"
        data_dict["landing_image"] = landing_image_record

    # animation
    img_string = data["add an animation"].strip()

    if img_string == "_No response_":
        msg_log += "**Animation**\n"
        msg_log += "Warning: No animation uploaded.\n\n"
        data_dict["animation"] = empty_image_record
    else:
        animation_record, log = parse_image_and_caption(img_string, "animation")
        if log:
            msg_log += "**Animation**\n" + log + "\n"
        data_dict["animation"] = animation_record

    # graphic abstract
    img_string = data["add a graphic abstract figure"].strip()

    if img_string == "_No response_":
        msg_log += "**Graphic abstract**\n"
        msg_log += "Warning: No image uploaded.\n\n"
        data_dict["graphic_abstract"] = empty_image_record
    else:
        graphic_abstract_record, log = parse_image_and_caption(img_string, "graphic_abstract")
        if log:
            msg_log += "**Graphic abstract**\n" + log + "\n"
        data_dict["graphic_abstract"] = graphic_abstract_record

    # model setup figure
    img_string = data["add a model setup figure"].strip()

    if img_string == "_No response_":
        msg_log += "**Model setup figure**\n"
        msg_log += "Warning: No image uploaded.\n\n"
        data_dict["model_setup_figure"] = empty_image_record
    else:
        model_setup_fig_record, log = parse_image_and_caption(img_string, "model_setup")
        if log:
            msg_log += "**Model setup figure**\n" + log + "\n"
        data_dict["model_setup_figure"] = model_setup_fig_record

    # description
    model_description = data["add a description of your model setup"].strip()

    if model_description == "_No response_":
        msg_log += "**Model setup description**\n"
        msg_log += "Warning: No description given \n"
    else:
        data_dict["model_setup_description"] = model_description

    # Add dateSubmitted
    data["dateSubmitted"] = datetime.now().isoformat()

    return data_dict, msg_log
