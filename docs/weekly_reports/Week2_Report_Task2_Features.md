# MGT 599 Capstone - Weekly Report
## Week 2 - Task 2 Feature Engineering
Group 4 | April 2026

## 1. Description of Work

My role this week was to build the features for Task 2, which is the subindustry classification problem. Task 2 is more granular than Task 1 - instead of predicting a broad industry label for a company, we are predicting the subindustry for each individual business segment that a company operates in. The main text column I worked with is SegmentDescription, which describes what each segment actually does.

The question I was trying to answer was: what information from the text descriptions can we turn into numbers that will help a model tell the difference between subindustries? A segment described as doing "cloud-based software delivery" should look very different from one doing "retail banking" - but only if we convert that language into the right features.

I built the features in three layers.

The first layer was basic text statistics - how long is the description in characters, how many words does it have, how many of those words are unique, what is the average word length, and whether the description field even has any content. These are simple but give the model a sense of how much information is available per row.

The second layer was keyword flags. I made a list of words that tend to appear in specific subindustries - things like "cloud," "saas," "brokerage," "logistics," "warehousing," "staffing," "leasing," and others. For each row, I checked whether each keyword appears in the segment description and stored that as a 1 or 0 column. I used 26 keywords in total covering a range of subindustry activity types.

The third layer was TF-IDF features. I ran TF-IDF on the SegmentDescription column alone to get 300 features, and then again on all text columns combined into a single string to get another 300 features. The idea behind the combined version is that a segment might have additional context in other text fields that helps identify its subindustry.

I also added a flag column called short_desc_flag that marks any row where the segment description has fewer than 5 words. Those rows are going to be hard for any model to classify because there is simply not enough text to work with.

## 2. Summary of Findings

Task 2 has more classes than Task 1 and the imbalance is severe. A small number of subindustry labels dominate the dataset and there are many labels with fewer than 10 records. This is the single biggest challenge going into modeling.

The keyword analysis showed that words like "software," "retail," "manufacturing," and "consulting" were the most common hits across the dataset. More specific terms like "saas," "brokerage," and "staffing" had much lower hit rates but those are likely to be more informative because they are specific to narrow subindustries.

The TF-IDF on the combined text columns produced 300 features that capture broader context than just the segment description alone. My expectation is that this version will outperform the single-column TF-IDF in Week 3 testing, but we will only know for sure after we run the models.

Short descriptions were a notable issue in Task 2. Some segment descriptions were either blank or only had one or two words. These are flagged and will likely be among the hardest rows to correctly classify.

## 3. Supporting Outputs

My script is scripts/task2_features.py in the shared repository:
https://github.com/venomez-viper/Classification-Project

The script reads from data/cleaned/task2_clean.csv and writes four output files to outputs/features/task2/:

task2_features_basic_v1.csv - the original data with text stats and keyword flag columns added

task2_tfidf_features_v1.csv - 300 TF-IDF features computed from the SegmentDescription column

task2_combined_tfidf_v1.csv - 300 TF-IDF features computed from all text columns combined

task2_features_full_v1.csv - the basic features and TF-IDF merged into one file for modeling

The model review script then ran on task2_features_full_v1.csv and produced the final clean version at outputs/model_ready/task2_model_ready_v1.csv.

The full pipeline including my output is documented in the descriptive_analytics.html file in the docs/ folder of the repository.

## 4. Reflection

The main challenge on my end was choosing the right keywords for the keyword flag layer. Subindustries are very diverse and some of them have descriptions that do not contain obvious single words that identify them. I had to think carefully about which terms would actually differentiate subindustries rather than appearing everywhere. I settled on 26 keywords but there is room to expand this list in Week 3 if the model struggles with certain categories.

I also had to make sure my script was reading from the cleaned CSV correctly and writing to the right output folder. The shared common_utils.py file handled most of the path management so I did not have to worry about hardcoding directories.

One thing I noticed is that the combined text TF-IDF and the single column TF-IDF will produce overlapping vocabulary. We may want to experiment with using only one of them in the final model to avoid redundant features.

For next week I plan to help evaluate which feature set works better for Task 2 - basic features only, single TF-IDF, or combined TF-IDF. Depending on the results we may also go back and expand the keyword list for subindustries that the model consistently gets wrong.
