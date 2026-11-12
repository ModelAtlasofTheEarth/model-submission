#provides a mapping between keys in the ro-crate dictionary (left)
#and keys in issue dictionary (which are the values in the mapping)
#None value indicate default values or properties which we not attempt to automatically fill
#they should nothing apart from map between

root_node_mapping = {"@id":"./",
            "identifier": None,
            "@type":None,
            "alternateName":"slug",
            "name":"title",
            #abstract is generally taken from associated_publication
            "abstract":"abstract",
            #description used for brief plain language summary
            "description":"description",
            "creator":"creators",
            #"contributor":"contributor",
            "citation":"publication",
            "publisher":None,
            "license":"license",
            "keywords":"model_keywords",
            "about":"for_codes",
            "funder":"funder",
            "funding":"funding",
            "version":None,
            "temporalCoverage":None,
            "Spatial extents":None,
            "spatialCoverage":None,
            "isBasedOn":None,
            "isPartOf":None,
            "creativeWorkStatus":"model_status"
            }


model_inputs_node_mapping = {"@id":None,
             "identifier": ["model_code_inputs.doi"],
             "url": "model_code_inputs.links",
             "@type":None,
            #the 'model input usage / reproducibility' answer; replaces the template's placeholder description
            "description":"model_code_inputs.notes",
            "creator":"creators",
            "version":None,
            "programmingLanguage":None,
            "keywords":None,
            "runtimePlatform":None,
            "memoryRequirements":None,
            "processorRequirements":None,
            "storageRequirements":None}


model_outputs_node_mapping = {"@id":"model_output_data",
            #the list around certain items in the mapping cause the same structure to appear in the RO-Crate
            "identifier": ["model_output_data.doi"],
            "@type":None,
            "description":"model_output_data.notes",
            "creator":"model_output_data.creators",
            "version":None,
            "programmingLanguage":None,
            "contentSize":"model_output_data.size",
            "fileFormat":None,
            }

website_material_node_mapping = {"@id":None,
            "@type":None,
            "description":None,
            "creator":"creators",
            "fileFormat":None
            }


dataset_creation_node_mapping = {"@id":"#datasetCreation",
            "@type":None,
            "agent":"model_output_data.creators",
            "description":None,
            "startTime":None,
            "endTime":None,
            "instrument":["software", "computer_resource"],
            "object":None,
            "result":None}

default_issue_entity_mapping_list = [root_node_mapping,
                model_inputs_node_mapping,
                model_outputs_node_mapping,
                website_material_node_mapping,
                dataset_creation_node_mapping]
