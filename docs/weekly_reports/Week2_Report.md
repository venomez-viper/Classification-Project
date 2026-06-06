# MGT 599 Capstone - Weekly Report
## Week 2
Group 4 | April 2026

## 1. Description of Work

This week our goal was to get the data cleaned, understand what we are working with, and prepare it for modeling in Week 3. We split the work into five areas so everyone could work on their part at the same time without getting in each other's way.

The first thing we did was load the raw company data into a database using DuckDB and run validation checks to make sure the tables loaded correctly. From there we cleaned both datasets - trimming extra whitespace, replacing blank strings with proper null values, and standardizing column types. We saved the cleaned versions as CSV files that everyone on the team could use.

What we were trying to figure out in this step: is the data structured well enough to build a classifier on? How complete are the descriptions? How many unique labels are there and how are they distributed?

After cleaning we did a full descriptive analysis of both datasets. We looked at missing values, the distribution of industry and subindustry labels, revenue statistics, and the text descriptions in detail - things like how long they are on average, how many words they contain, and which words appear most frequently.

The last major piece this week was feature engineering. Since the classification targets are text descriptions, we needed to convert those into numbers the model can learn from. We built three types of features. First, basic text stats like character length, word count, and unique word count. Second, keyword flags - if a company description contains words like "bank" or "software" it gets a 1 for that column and 0 otherwise. Third, TF-IDF features which score each word based on how specifically it appears in certain companies compared to all others. We ran TF-IDF on the main description column and separately on all text columns combined to see if using more text improves things.

The final step was a quality check on the feature files - dropping any columns where almost every row had the same value since those are not useful for a model, and verifying that row counts were consistent throughout the pipeline.

## 2. Summary of Findings

The biggest thing we found is that class imbalance is going to be a real problem. In Task 1 (industry classification) a few industries have thousands of examples but a large number of industries have fewer than 10 records each. The top 3 classes alone cover a significant share of the entire dataset. Task 2 (subindustry classification) has an even larger label space and has the same imbalance issue. If we do not handle this the model will just learn the common categories and ignore the rare ones.

We also found that revenue is very skewed. The median is much lower than the mean which means there are a few extremely large companies pulling the average up. This is worth keeping in mind if we decide to use revenue as a feature - we would need to apply a log transformation to make it useful.

On the text side, we found that the descriptions do contain industry-specific vocabulary. Words like "lending," "cloud," "semiconductor," and "brokerage" show up in clusters that align with specific industries. This is encouraging because it means TF-IDF should produce meaningful features. However, some rows have very short or empty descriptions. We flagged those rows and will need to decide how to handle them in modeling.

The combined TF-IDF (from all text columns together) gave us 300 additional features on top of the single-column TF-IDF. Our hypothesis going into Week 3 is that the combined version will perform better since it captures signal from multiple fields.

## 3. Supporting Outputs

The pipeline code, notebooks, and generated HTML files are all available in the project repository at:
https://github.com/venomez-viper/Classification-Project

The rendered notebook exports (HTML with all code, outputs, and visualizations included) are in the docs/ folder of the repository:
- week2_submission.html - full week 2 pipeline with outputs
- descriptive_analytics.html - complete descriptive analytics report with charts

Feature files generated this week are stored locally (not tracked in git due to file size):
- outputs/features/task1/ - four CSV files with Task 1 features
- outputs/features/task2/ - four CSV files with Task 2 features
- outputs/model_ready/ - final cleaned feature files ready for modeling

## 4. Reflection

The main challenge this week was setting up the parallel workflow so five people could work on the same codebase without conflicts. We solved this by creating a shared utility file (common_utils.py) that everyone imports from, and keeping each person's work in a separate script that writes to a separate output folder. This worked well and we had no file conflicts during the week.

We ran into a few technical issues along the way. The first was a data type bug in the cleaning step where a numeric column (MstarGlobal) was being incorrectly cast to a text type. We caught this during validation and fixed it in the cleaner. The second was a variable scoping bug in the model review script where columns being dropped inside a loop were not actually updating the main dataframe. Both were fixed before the final output files were generated.

Setting up the notebook export to HTML also took longer than expected because we had to install the Jupyter kernel separately and deal with some IDE metadata that was interfering with the export tool.

For next week our plan is to train baseline classifiers on the model-ready files. We are going to start with Logistic Regression and Random Forest since they are interpretable and give us a strong baseline to compare against. We will evaluate using F1-macro score rather than accuracy because accuracy is misleading when the classes are as imbalanced as ours are. We also want to compare TF-IDF from a single column versus the combined column version to see which one actually performs better in practice.
