# Welcome to the Model Atlas of The Earth (M@TE) 

<p align="center">
  <a href="https://github.com/ModelAtlasofTheEarth/model-submission/issues/new?template=model_submission.yml">
    <img src="https://img.shields.io/badge/Make%20Submission-%20%E2%96%B6%20-blue?style=for-the-badge&logo=github" alt="Make Submission" />
  </a>
</p>

## Model submission workflow:

**1) Make a new model request:**
* open a new issue using the [New model request](https://github.com/ModelAtlasofTheEarth/model-submission/issues/new/choose)
* fill in as much information as you can and submit the issue
* a https://github.com/ModelAtlasofTheEarth/model-submission/labels/new%20model label will appear on the original issue
* This will trigger workflows that collect this information and source additional metadata relavant to your model
* You will see a summary report for your model, including potential missing information or errors (e.g. URLs that didn't resolve)
* If you have requested the content of your model to be embargoed, you should see an https://github.com/ModelAtlasofTheEarth/model-submission/labels/embargo%20requested label. We can still create a model repository, metadata file, and DOI for this model
  

**2) Editing and review:**

* By editing the first comment in the issue discussion, you will trigger a rebuild of the model information
* When you are satisfied with the information contained in the report, add a https://github.com/ModelAtlasofTheEarth/model-submission/labels/review%20requested label to the issue

**3) Model repository creation:**
* The [model_reviewers](https://github.com/orgs/ModelAtlasofTheEarth/teams/model_reviewers) team will add an https://github.com/ModelAtlasofTheEarth/model-submission/labels/model%20approved label to the issue
* this triggers the creation of a new model repository within the M@TE organization, based on [this simple template](https://github.com/ModelAtlasofTheEarth/mate_model_template)
* the model metadata is stored as an [RO-Crate](https://www.researchobject.org/ro-crate/) (named `ro-crate-metadata.json`) in the top level of the repository
* A https://github.com/ModelAtlasofTheEarth/model-submission/labels/model%20created label will appear on your issue
* The github account holder who submitted the model will have owner privillages.


**4) Clone and configure your model repository:**

* Your model repository is now yours to customize and fill with files (payload)
* We encourage you to use github to add any material that is within github's typical repository limits (files < 100 Mb, total repository size < 5 Gb)
* You may customize the model repository as you feel fit. This may require editing of the metadata file () to reflect changes in directory structure
* Push any changes back to the [M@TE organization](https://github.com/ModelAtlasofTheEarth/).  

**5) Upload model to our [NCI](https://nci.org.au/) Server:**
* Add an https://github.com/ModelAtlasofTheEarth/model-submission/labels/upload%20to%20NCI label to the model submission issue
* Let us know (via the original issue) if you need to add additional files that exceed Github's limits
  * The [model_reviewers](https://github.com/orgs/ModelAtlasofTheEarth/teams/model_reviewers) team will contact you via email to orchestrate this process

**6) Model published:**
* Your model will be published on the NCI [GeoNetworkCatalog](https://geonetwork.nci.org.au/geonetwork/srv/eng/catalog.search#/home)
* It will recieve a DOI and this will be automatically added to your model metadata
* Your model will be featured on the M@TE website
* a https://github.com/ModelAtlasofTheEarth/model-submission/labels/model%20published label will appear on the original issue

## Links

* [M@TE website](https://mate.science)
* [NCI Data Catalogue](https://geonetwork.nci.org.au/geonetwork/)
* [AuScope](https://www.auscope.org.au/)

## Motivation and further reading

* [RO-Crates](https://www.researchobject.org/ro-crate/)
* [a-decade-of-open-data-in-research](https://scholarlykitchen.sspnet.org/2022/03/30/guest-post-a-decade-of-open-data-in-research-real-change-or-slow-moving-compliance/?informz=1)
* [what-is-fair-for-geodynamics?](https://blogs.egu.eu/divisions/gd/2020/07/24/what-is-fair-for-geodynamics/)
* [comses.net](comses.net)
* [codemeta](https://codemeta.github.io/index.html)




