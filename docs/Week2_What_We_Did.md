# Week 2 Summary - MGT 599 Capstone
April 2026

## What this project is about

We have a dataset of company descriptions - text that describes what each company does, how much revenue it makes, what segment of business they operate in. Someone already went through and labeled a lot of these companies with the right industry (like Finance or Healthcare) or subindustry (like Cloud Software or Retail Banking).

Our goal is to build a machine learning model that can read a company description and predict those labels automatically. So instead of a person having to label every new company by hand, the model does it.

This week was the setup phase. We cleaned the data, explored it, and prepared it so we can run the actual model next week.

## The two classification tasks

Task 1 - predict which industry a company belongs to. We use the company's long text description (column called LongProfile) to make that prediction. The label we are predicting is called MstarGlobal. The data file is task1_clean.csv.

Task 2 - predict which subindustry a company segment belongs to. Here we use the segment description (SegmentDescription). The label is called Subindustry. The data file is task2_clean.csv.

## What each person did

Member 1 (Lead) - ran lead_tracking.py. Set up all the project folders, created the team progress tracker spreadsheet, made templates for the weekly report and handoff notes. Also ran the file audit at the end to check what output files exist.

Member 2 (Dashboard) - ran dashboard.py and the descriptive_analytics notebook. Loaded both datasets, made the class distribution charts, missing value tables, text length histograms, and wrote up a findings summary. Output files went to outputs/dashboard/.

Member 3 (Task 1 Features) - ran task1_features.py. Did all the feature engineering for the industry task - text stats, keyword flags, TF-IDF. Output files went to outputs/features/task1/.

Member 4 (Task 2 Features) - ran task2_features.py. Same thing as Task 1 but for the subindustry task with different keywords. Output files went to outputs/features/task2/.

Member 5 (Model Review) - ran model_ready.py. Reviewed both feature files, dropped any columns that were useless (near-constant), checked row counts, and saved the final model-ready CSVs to outputs/model_ready/.

## What files were created this week

Data pipeline (run main.py first):
- data/cleaned/task1_clean.csv - cleaned version of Task 1 data
- data/cleaned/task2_clean.csv - cleaned version of Task 2 data

Task 1 feature files (in outputs/features/task1/):
- task1_features_basic_v1.csv - original data plus text stats and keyword columns
- task1_tfidf_features_v1.csv - 300 TF-IDF columns from the main text column
- task1_combined_tfidf_v1.csv - 300 TF-IDF columns from all text columns together
- task1_features_full_v1.csv - everything merged into one file

Task 2 feature files (in outputs/features/task2/):
- same four files but for Task 2

Model-ready files (in outputs/model_ready/):
- task1_model_ready_v1.csv - final Task 1 file, ready for modeling
- task2_model_ready_v1.csv - final Task 2 file, ready for modeling

Notebooks:
- notebooks/descriptive_analytics.ipynb - full analytics with charts
- notebooks/week2_submission.ipynb - complete submission notebook

## What we found in the data

The labels are not evenly spread. A few industries have thousands of examples but a lot of the smaller industries have fewer than 10 records each. This is called class imbalance. It matters because if we just train a model without dealing with it, the model will mostly learn the common industries and do badly on the rare ones. We need to handle this in Week 3.

Some company descriptions are empty or really short (under 5 words). We added a column called short_desc_flag to mark those rows. The model won't be able to do much with blank text, so we need to think about how to handle those.

Revenue numbers are very spread out. Most companies have normal revenue but there are some very large outliers that pull the average way up. The median is a better number to use here. We might apply a log transformation to revenue when we use it as a feature.

The company data is at the segment level, not the company level. So one company might have 5 or 10 rows in the dataset - one per business segment. Task 2 is focused on those segments.

The text descriptions do have meaningful signals - words like "lending", "semiconductor", "cloud" appear a lot in specific industries. That's what TF-IDF is capturing.

## What TF-IDF actually is

TF-IDF is a way to turn text into numbers. It looks at all the words in all the descriptions and figures out which words are useful for telling companies apart. Common words like "the" or "and" that appear everywhere get low scores. Specific words like "semiconductor" or "brokerage" that only appear in certain companies get high scores. Each company ends up with 300 numbers representing how strongly those useful words appear in their description.

## What the shared utility file does

common_utils.py is a shared file that all five team scripts import from. It has the helper functions that everyone needs - loading the data, saving files, text cleaning, TF-IDF setup, the folder paths, etc. We put it in one place so nobody duplicates code and changes in one place apply everywhere.

## What comes next (Week 3)

We take the model-ready files and train classifiers on them. We are planning to try Logistic Regression and Random Forest to start. We will measure accuracy and F1-macro score (F1-macro is better for imbalanced datasets because it gives equal weight to all classes, not just the common ones). We will also compare TF-IDF from one column vs combined columns to see which gives better predictions.

## Questions that might come up

What is the goal? We are building a model that reads a company's text description and automatically assigns it the right industry or subindustry label.

What data are you using? Two cleaned CSV files from the capstone dataset - task1_clean.csv for industry classification and task2_clean.csv for subindustry classification.

Why TF-IDF? Machine learning models cannot process raw text. TF-IDF converts words into numbers in a way that preserves the important signals - words that are specific to certain industries get higher weights.

What problems did you find? Class imbalance is the biggest one. Some industry categories have thousands of examples, others have fewer than 10. We also found some rows with missing or very short descriptions.

How did the team work in parallel? Each person has a separate script in the scripts/ folder that reads from the same cleaned CSV files but writes to a different output folder. So there are no conflicts when running at the same time.

MGT 599 Capstone - Week 2
