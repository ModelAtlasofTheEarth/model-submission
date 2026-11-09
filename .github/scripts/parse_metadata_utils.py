import html
import re


def extract_publication_abstract(value):
    """Return readable abstract text from Crossref/JATS or plain text input."""
    if isinstance(value, list):
        value = "\n".join(str(item) for item in value if item is not None)
    if not value:
        return ""

    text = html.unescape(str(value))
    # Preserve paragraph boundaries before stripping XML/HTML tags.
    text = re.sub(r"<\s*/?\s*(?:jats:)?(?:p|br)\s*/?\s*>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    return text.strip()


def parse_author(metadata):
    """
    BY_AI: Parses an author metadata record into a schema.org Person dictionary.

    Accepts either a pre-formed JSON-LD record (containing '@type' and '@id') or a
    raw ORCID API response. In the latter case, it extracts the person's name and any
    current employment affiliations.

    Parameters:
        metadata (dict): A metadata record, either already in JSON-LD format or a raw
            ORCID API response.

    Returns:
        tuple:
            author_record (dict): A schema.org Person dictionary with keys such as
                '@type', '@id', 'givenName', 'familyName', and optionally 'affiliation'.
            log (str): A log string recording success messages or errors encountered
                during parsing.
    """
    log = ""
    author_record = {}

    if "@type" and "@id" in metadata.keys():
        author_record = metadata
        log += "ORCID metadata record succesfully extracted in json-ld format \n"

    else:
        try:
            author_record = {
                "@type": "Person",
                "@id": metadata["orcid-identifier"]["uri"],
                "givenName": metadata["person"]["name"]["given-names"]["value"],
                "familyName": metadata["person"]["name"]["family-name"]["value"],
            }

            affiliation_list = []
            for affiliation in metadata["activities-summary"]["employments"][
                "affiliation-group"
            ]:
                summary = affiliation["summaries"][0]["employment-summary"]
                if summary["end-date"] is None:
                    affiliation_list.append(
                        {
                            "@type": "Organization",
                            "name": summary["organization"]["name"],
                        }
                    )

            if affiliation_list:
                author_record["affiliation"] = affiliation_list

        except Exception as err:
            log += "Error: unable to parse author metadata. \n"
            log += f"`{err}`\n"

    return author_record, log


def parse_organization(record):
    """
    Parses a ROR organization record into a schema.org Organization dict.
    Handles both legacy and current ROR formats.
    """
    log = ""

    if not record or "id" not in record:
        return {}, "Error: invalid or empty organization record.\n"

    try:
        org = {"@type": "Organization"}
        org["@id"] = record.get("id")

        # ✅ Handle modern ROR format (name inside 'names' list)
        if "name" in record and isinstance(record["name"], str):
            org["name"] = record["name"]
        elif (
            "names" in record and isinstance(record["names"], list) and record["names"]
        ):
            org["name"] = record["names"][0].get("value", "")
        else:
            org["name"] = "(unknown name)"
            log += "Warning: missing name field.\n"

        # Add homepage if available
        links = record.get("links", [])
        if links:
            if isinstance(links[0], dict):
                org["url"] = links[0].get("value")
            else:
                org["url"] = links[0]

        # Add organization types if available
        if record.get("types"):
            org["additionalType"] = record["types"]

        return org, log

    except Exception as e:
        return {}, f"Error: unable to parse organization metadata.\n`{e}`\n"


def parse_software(metadata, doi):
    """
    BY_AI: Parses software metadata into a schema.org SoftwareApplication dictionary.

    Accepts either a pre-formed JSON-LD record or raw metadata (e.g., from a Zenodo
    DOI response). Falls back to constructing a SoftwareApplication entity from
    available fields such as title, version, and creators.

    Parameters:
        metadata (dict): A metadata record, either already in JSON-LD format or a raw
            API response containing software information.
        doi (str): The DOI or URL used as the '@id' for the software entity when one
            cannot be derived from the metadata itself.

    Returns:
        tuple:
            software_record (dict): A schema.org SoftwareApplication dictionary with
                keys such as '@type', '@id', 'name', 'softwareVersion', and 'author'.
            log (str): A log string recording success messages or errors encountered
                during parsing.
    """
    log = ""
    software_record = {}

    # here we check if software metdata was found in json-ld
    # if so, we simply return the record
    if "@type" and "@id" in metadata.keys():
        software_record = metadata
        log += "doi.org metadata record succesfully extracted in json-ld format \n"

    # if not, we'll try to a schema.org entity from the json
    else:
        software_record["@type"] = "SoftwareApplication"
        software_record["@id"] = doi
        # try:
        found_something = False
        if "title" in metadata.keys():
            software_record["name"] = metadata["title"]
            print("found title")
            found_something = True
        if "metadata" in metadata.keys():
            if "version" in metadata["metadata"].keys():
                software_record["softwareVersion"] = metadata["metadata"]["version"]
                found_something = True

            if "creators" in metadata["metadata"].keys():
                author_list = []

                for author in metadata["metadata"]["creators"]:
                    author_record = {"@type": "Person"}
                    if "orcid" in author:
                        author_record["@id"] = author["orcid"]
                    if "givenName" in author:
                        author_record["givenName"] = author["given"]
                        author_record["familyName"] = author["family"]
                    elif "name" in author:
                        author_record["name"] = author["name"]
                    if "affiliation" in author:
                        author_record["affiliation"] = author["affiliation"]

                    author_list.append(author_record)

            if author_list:
                found_something = True
                software_record["author"] = author_list

        # except Exception as err
        if found_something is False:
            log += "Error: unable to parse software metadata. \n"
            # log += f"`{err}`\n"

    return software_record, log


def parse_publication(metadata):
    """
    BY_AI: Parses a Crossref API response into a schema.org ScholarlyArticle dictionary.

    Accepts either a pre-formed JSON-LD record or a raw Crossref API response wrapped
    in a 'message' key. Extracts bibliographic details including title, DOI, authors,
    abstract, publication issue/volume information, funder details, and pagination.

    Parameters:
        metadata (dict): A Crossref API response dict containing a 'message' key, or
            a pre-formed JSON-LD record with '@type' and '@id'.

    Returns:
        tuple:
            publication_record (dict): A schema.org ScholarlyArticle dictionary with
                keys such as '@type', '@id', 'name', 'author', 'abstract',
                'isPartOf', and 'funder'.
            log (str): A log string recording success messages or errors encountered
                during parsing.
    """
    log = ""
    publication_record = {}

    metadata = metadata["message"]

    if "@type" and "@id" in metadata.keys():
        publication_record = dict(metadata)
        abstract = extract_publication_abstract(publication_record.get("abstract"))
        if abstract:
            publication_record["abstract"] = abstract
        elif "abstract" in publication_record:
            publication_record.pop("abstract")
        log += "Crossref metadata record succesfully extracted in json-ld format \n"
    else:
        try:
            publication_record = {
                "@type": "ScholarlyArticle",
                "@id": metadata["URL"],
                "name": metadata["title"][0],
            }

            if "issue" in metadata:
                publication_issue = (
                    {
                        "@type": "PublicationIssue",
                        "issueNumber": metadata["issue"],
                        "datePublished": "-".join(
                            map(str, metadata["published"]["date-parts"][0])
                        ),
                        "isPartOf": {
                            "@type": ["PublicationVolume", "Periodical"],
                            "name": metadata["container-title"],
                            "issn": metadata["ISSN"],
                            "volumeNumber": metadata["volume"],
                            "publisher": metadata["publisher"],
                        },
                    },
                )

                publication_record["isPartOf"] = publication_issue
            else:
                if metadata["published"]:
                    publication_record["datePublished"] = "-".join(
                        map(str, metadata["published"]["date-parts"][0])
                    )
                if metadata["publisher"]:
                    publication_record["publisher"] = metadata["publisher"]

            author_list = []

            for author in metadata["author"]:
                author_record = {"@type": "Person"}
                if "ORCID" in author:
                    author_record["@id"] = author["ORCID"]
                author_record["givenName"] = author["given"]
                author_record["familyName"] = author["family"]

                affiliation_list = []
                for affiliation in author["affiliation"]:
                    affiliation_list.append(
                        {"@type": "Organization", "name": affiliation["name"]}
                    )

                if affiliation_list:
                    author_record["affiliation"] = affiliation_list

                author_list.append(author_record)

            if author_list:
                publication_record["author"] = author_list

            abstract = extract_publication_abstract(metadata.get("abstract"))
            if abstract:
                publication_record["abstract"] = abstract

            if "page" in metadata:
                publication_record["pagination"] = metadata["page"]

            if "alternative-id" in metadata:
                publication_record["identifier"] = metadata["alternative-id"]

            if "funder" in metadata:
                funder_list = []
                for funder in metadata["funder"]:
                    funder_list.append(
                        {"@type": "Organization", "name": funder["name"]}
                    )
                publication_record["funder"] = funder_list

        except Exception as err:
            log += "Error: unable to parse publication metadata. \n"
            log += f"`{err}`\n"

    return publication_record, log
