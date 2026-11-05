import json
from ro_crate_utils import *
from crosswalk_mappings import *
from nci_iso_tools import *
import copy
import pandas as pd
from config import MATE_GADI


def dict_to_report(issue_dict, verbose=False):
    """
    Generates a detailed report in Markdown format based on the provided issue dictionary.The function supports a verbose mode that includes additional details such as software framework authors and a dictionary dump for testing purposes.

    Parameters:
        issue_dict (dict): A dictionary containing all the necessary information to generate the report.
        verbose (bool, optional): If True, includes additional details in the report. Default is False.

    Returns:
        str: A string containing the complete report in Markdown format.
    """

    #############
    # Section 1
    #############
    report = "## Section 1: Summary of your model   \n\n"
    # contributor
    report += "**Model Submitter:**  \n\n"
    report += f"{issue_dict['submitter']['givenName']} {issue_dict['submitter']['familyName']} "
    if "@id" in issue_dict["submitter"]:
        report += f"([{issue_dict['submitter']['@id'].split('/')[-1]}]({issue_dict['submitter']['@id']}))"

    report += "\n\n"

    # model creators(s)
    report += "**Model Creator(s):**  \n\n"
    for creator in issue_dict["creators"]:
        report += f"- {creator['givenName']} {creator['familyName']} "
        if "@id" in creator:
            report += f"([{creator['@id'].split('/')[-1]}]({creator['@id']}))"
        report += "  \n"
    report += "  \n"

    # slug, this gets mapped to name. This is what the model is called on NCI
    report += "**Model slug:**  \n\n"
    report += (
        f"`{issue_dict['slug']}` \n\n"
        + "(this will be the name of the model repository when created) \n\n"
    )

    # title. Note title doesn't appear in CreativeWorks. This gets mapped to alternateName.
    report += "**Model name:**  \n\n"
    report += f"_{issue_dict['title']}_  \n\n"

    # license
    report += "**License:**  \n\n"
    if "url" in issue_dict["license"]:
        report += f"[{issue_dict['license']['description']}]({issue_dict['license']['url']})\n\n"
    else:
        report += f"{issue_dict['license']['description']}\n\n"

    # model category
    report += "**Model Category:**  \n\n"
    for category in issue_dict["model_category"]:
        report += f"- {category}   \n"
    report += "  \n"

    # model category
    report += "**Model Status:**  \n\n"
    for status in issue_dict["model_status"]:
        report += f"- {status}   \n"
    report += "  \n"

    # associated publication DOI
    if "@id" in issue_dict["publication"]:
        report += "**Associated Publication title:**  \n\n"
        report += f"_[{issue_dict['publication']['name']}]({issue_dict['publication']['@id']})_ \n\n"

    # description
    report += "**Short description:**  \n\n"
    report += issue_dict["description"] + "\n\n"

    # abstract
    report += "**Abstract:**  \n\n"
    report += issue_dict["abstract"] + "\n\n"

    # scientific keywords
    if issue_dict["scientific_keywords"]:
        report += "**Scientific Keywords:**  \n\n"
        for keyword in issue_dict["scientific_keywords"]:
            report += f"- {keyword}   \n"
        report += "  \n"

    # funder
    report += "**Funder(s):**  \n"
    for funder in issue_dict["funder"]:
        if "name" in funder.keys():
            report += f"- {funder['name']} "
            if "@id" in funder:
                report += f"({funder['@id']})"
            elif "url" in funder:
                report += f"({funder['url']})"
            report += "  \n"
    report += "  \n"

    #############
    # Section 2
    #############

    report += "## Section 2: your model code, output data  \n\n"

    # include model code
    if "embargo" in issue_dict:
        if issue_dict["embargo"][0] is True:
            report += "**Embargo on model contents requested until:**   \n\n"
            report += f"{issue_dict['embargo'][1]} \n\n"
        else:
            report += "**No embargo on model contents requested** \n\n"

    # include model code
    if "include_model_code" in issue_dict:
        report += "**Include model code:**   \n\n"
        report += f"{str(issue_dict['include_model_code'])} \n\n"

    # model code URI/DOI
    if issue_dict["model_code_inputs"].get("links"):
        report += "**Model links:**   \n\n"
        report += "\n".join(issue_dict["model_code_inputs"]["links"]) + "\n\n"

    if issue_dict["model_code_inputs"]["doi"]:
        report += "**Model code existing URL/DOI:**   \n\n"
        report += f"{issue_dict['model_code_inputs']['doi']} \n\n"

    # model code notes
    if issue_dict["model_code_inputs"]["notes"]:
        report += "**Model code notes:**   \n\n"
        report += f"{issue_dict['model_code_inputs']['notes']} \n\n"

    # include model output data
    if "include_model_output" in issue_dict:
        report += "**Include model output data:**   \n\n"
        report += f"{str(issue_dict['include_model_output'])} \n\n"

    # model output URI/DOI
    if issue_dict["model_output_data"]["doi"]:
        report += "**Model output data, existing URL/DOI:**   \n\n"
        report += f"{issue_dict['model_output_data']['doi']} \n\n"

    # model output notes
    if issue_dict["model_output_data"]["notes"]:
        report += "**Model output data notes:**   \n\n"
        report += f"{issue_dict['model_output_data']['notes']} \n\n"

    #############
    # Section 3
    #############
    report += "## Section 3: software framework and compute details   \n"
    software_records = issue_dict.get("software", [])
    if isinstance(software_records, dict):
        software_records = [software_records]
    for software_number, software in enumerate(software_records, start=1):
        report += f"### Software framework {software_number}\n\n"
        if "@id" in software:
            report += "**Software Framework DOI/URL:**  \n\n"
            report += f"Found software: _[{software.get('name', 'Unnamed software')}]({software['@id']})_ \n\n"

        if "codeRepository" in software:
            report += "**Software Repository:**   \n\n"
            report += f"{software['codeRepository']} \n\n"

        if "name" in software:
            report += "**Name of software framework:**  \n\n"
            report += f"{software['name']} \n\n"

        if "softwareVersion" in software:
            report += "**Software version used:**  \n\n"
            report += f"{software['softwareVersion']} \n\n"

        if verbose is True and "author" in software:
            report += "**Software framework authors:**  \n"
            for author in software["author"]:
                if "givenName" in author and "familyName" in author:
                    report += f"- {author['givenName']} {author['familyName']} "
                elif "name" in author:
                    report += f"- {author['name']} "
                if "@id" in author:
                    report += f"([{author['@id'].split('/')[-1]}]({author['@id']}))"
                report += "  \n"
            report += "  \n"

        if "keywords" in software:
            report += "**Software & algorithm keywords:**  \n\n"
            for keyword in software["keywords"]:
                report += f"- {keyword}   \n"
            report += "  \n"

    # computer URI/DOI
    if "computer_uri" in issue_dict:
        report += "**Computer DOI/URL:**   \n\n"
        report += f"{issue_dict['computer_uri']} \n\n"

    #############
    # Section 4
    #############
    report += "## Section 4: web material (for mate.science)   \n"
    # landing page image and caption
    if "landing_image" in issue_dict:
        report += "**Landing page image:**  \n\n"
        if "filename" in issue_dict["landing_image"]:
            report += f"Filename: [{issue_dict['landing_image']['filename']}]({issue_dict['landing_image']['url']})  \n"
        if "caption" in issue_dict["landing_image"]:
            report += f"Caption: {issue_dict['landing_image']['caption']}  \n"
        report += "  \n"

    # animation
    if "animation" in issue_dict:
        report += "**Animation:**  \n\n"
        if "filename" in issue_dict["animation"]:
            report += f"Filename: [{issue_dict['animation']['filename']}]({issue_dict['animation']['url']})  \n"
        if "caption" in issue_dict["animation"]:
            report += f"Caption: {issue_dict['animation']['caption']}  \n"
        report += "  \n"

    # graphic abstract
    if "graphic_abstract" in issue_dict:
        report += "**Graphic abstract:**  \n\n"
        if "filename" in issue_dict["graphic_abstract"]:
            report += f"Filename: [{issue_dict['graphic_abstract']['filename']}]({issue_dict['graphic_abstract']['url']})  \n"
        if "caption" in issue_dict["graphic_abstract"]:
            report += f"Caption: {issue_dict['graphic_abstract']['caption']}  \n"
        report += "  \n"

    # model setup figure
    if "model_setup_figure" in issue_dict:
        report += "**Model setup figure:**  \n\n"
        if "filename" in issue_dict["model_setup_figure"]:
            report += f"Filename: [{issue_dict['model_setup_figure']['filename']}]({issue_dict['model_setup_figure']['url']})  \n"
        if "caption" in issue_dict["model_setup_figure"]:
            report += f"Caption: {issue_dict['model_setup_figure']['caption']}  \n"
        if "model_setup_description" in issue_dict:
            # report += "**Model setup description:**  \n"
            report += f"Description:  {issue_dict['model_setup_description']}\n\n"
        report += "  \n"

    return report


def dict_to_metadata(
    issue_dict,
    mapping_list=default_issue_entity_mapping_list,
    filter_entities=True,
    flat_compact_crate=True,
    timestamp=False,
    github_raw_base=None,
):
    """
    Converts an issue dictionary into a standardized metadata format using Research Object Crate (RO-Crate) structure,
    applying entity simplification and mappings based on predefined templates and rules.

    The function performs several key operations:
    - Filters and simplifies entities within the issue dictionary based on a specified template if `filter_entities` is True.
    - Loads a base RO-Crate template and applies direct mappings from the issue dictionary to the RO-Crate structure using `mapping_list`.
    - Allows for custom modifications to the RO-Crate based on specific data within the issue dictionary.
    - Optionally flattens the RO-Crate structure for a more compact representation if `flat_compact_crate` is True.

    Parameters:
    - issue_dict (dict): The issue dictionary containing data that needs to be converted into metadata.
    - mapping_list (list): A list of mappings that define how elements in the issue dictionary correspond to elements in the RO-Crate structure.
    - filter_entities (bool, optional): If True, simplifies entities in the issue dictionary using predefined templates. Defaults to True.
    - flat_compact_crate (bool, optional): If True, flattens the RO-Crate structure to bring nested entities to the top level. Defaults to True.

    Returns:
    - str: A JSON string representing the metadata in the RO-Crate format.

    Note:
    The function relies on external functions to load entity templates, apply mappings, and customize the RO-Crate. These functions need to be defined separately.
    """

    # Perform a deep copy of the issue_dict to avoid modifying the input dictionary
    issue_dict_copy = copy.deepcopy(issue_dict)

    # this takes the issue_dict and simplifies entities (e.g. @Type=Person) using templates defined at:
    # https://github.com/ModelAtlasofTheEarth/metadata_schema/blob/main/mate_ro_crate/type_templates.json
    if filter_entities is True:
        entity_template = load_entity_template()
        recursively_filter_key(issue_dict_copy, entity_template)

    # load the RO-Crate template as a Python dictionary
    # $print(ro_crate.keys())
    # >>>dict_keys(['@context', '@graph'])
    ro_crate = load_crate_template()

    # Apply direct mappings between the issue_dict and the RO-Crate
    dict_to_ro_crate_mapping(ro_crate, issue_dict_copy, mapping_list)

    # Add any further direct changes to the RO-Crate based on issue_dict
    defaults_and_customise_ro_crate(
        issue_dict_copy, ro_crate, timestamp=timestamp, github_raw_base=github_raw_base
    )

    # flatten the crate (brings nested entities to the top level)
    if flat_compact_crate is True:
        flatten_crate(ro_crate)
        # flatten a document
        # see: https://json-ld.org/spec/latest/json-ld/#flattened-document-form
        # all deep-level trees flattened to the top-level
        # ro_crate= jsonld.flatten(ro_crate)

    metadata_out = json.dumps(ro_crate)

    return metadata_out


def metadata_to_nci(ro_crate):
    """
    BY_AI: Converts an RO-Crate dictionary into an NCI/ISO metadata record as a pandas DataFrame.

    Transforms the flat '@graph' array of the RO-Crate into a nested dictionary keyed by
    entity ID, then extracts standard NCI metadata fields (title, abstract, license, field
    of research codes, etc.) along with author and funder rows. The result is a two-column
    DataFrame with 'Field' and 'Value' columns suitable for export as a CSV to the NCI
    data catalogue.

    Parameters:
        ro_crate (dict): An RO-Crate JSON-LD object containing at minimum a '@graph' key
            with a list of entity dictionaries, including a root entity ('@id': './').

    Returns:
        pandas.DataFrame: A DataFrame with columns ['Field', 'Value'] containing the NCI
            metadata fields, author rows, and funder rows concatenated in order.
    """

    # put the @graph array into a dictionary/nested format, where the @id field becomes the key
    ro_crate_nested = graph_to_nested_dict(ro_crate["@graph"])
    # extract funders and authors into a NCI/ISO format
    funders = extract_funder_details(ro_crate_nested)
    authors = extract_creator_details(ro_crate_nested)
    root = "root"  # Key for root element

    # build up any composite values
    nci_file_path = MATE_GADI + ro_crate_nested.get_nested(f"{root}.alternateName")

    fields_data = {
        "Title*": list_to_string(ro_crate_nested.get_nested(f"{root}.name")),
        "Dataset version*": list_to_string(
            ro_crate_nested.get_nested(f"{root}.version")
        ),
        "Abstract*": list_to_string(ro_crate_nested.get_nested(f"{root}.abstract")),
        "Topic category*": "geoscientificInformation",
        "Field of research (FOR)*": list_to_string(
            ro_crate_nested.get_nested(f"{root}.about.@id")
        ),
        "License*": ro_crate_nested.get_nested(f"{root}.license.description"),
        "Dataset lineage information*": list_to_string(
            ro_crate_nested.get_nested(f"{root}.description")
        ),
        "Dataset format*": "",
        "Dataset status": list_to_string(
            ro_crate_nested.get_nested(f"{root}.creativeWorkStatus")
        ),
        "Maintenance frequency*": "as needed",
        "Temporal extents* (if applicable)": "",
        "Spatial extents* (if applicable)": "",
        "Owner* (if applicable)": "",
        "Credit": "",
        "Supplemental or supporting material": "",
        "Local NCI file path": nci_file_path,
        "DOI (NCI Internal Field)": list_to_string(
            ro_crate_nested.get_nested(f"{root}.identifier")
        ),
        "Keyword/s": list_to_string(ro_crate_nested.get_nested(f"{root}.keywords")),
    }

    fields_df = pd.DataFrame(list(fields_data.items()), columns=["Field", "Value"])

    # update specific fields that need tailoring
    # ro_crate_data['@graph'][1]['alternateName']

    # fields_df
    # nci_file_path = ro_crate_nested.get_nested(f"{root}.alternateName")
    # "Local NCI file path": "",

    # Handling authors as before
    authors_rows = [
        {
            "Field": f"Author {i}",
            "Value": f"{author['Last name']}, {author['First name']}, {author['Organization']}, {author['Email']}, {author['ORCID ID']}",
        }
        for i, author in enumerate(authors, start=1)
    ]
    authors_df = pd.DataFrame(authors_rows)

    # Handling funders
    funder_rows = []
    for funder in funders:
        funder_rows.append(
            {"Field": "Organisation/funding agency name", "Value": funder["name"]}
        )
        funder_rows.append(
            {"Field": "Funding/award description or title", "Value": funder["grant_id"]}
        )
        funder_rows.append(
            {
                "Field": "Email address for the organisation/agency (if applicable)",
                "Value": funder["email"],
            }
        )
    funders_df = pd.DataFrame(funder_rows)

    # Concatenate all parts into a single DataFrame
    result_df = pd.concat([fields_df, authors_df, funders_df], ignore_index=True)
    return result_df
