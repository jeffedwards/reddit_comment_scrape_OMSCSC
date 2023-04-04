########################################################################################################################
# Instructions

# Get Reddit API keys from here: https://www.reddit.com/prefs/apps
# Update variables and setting as desired
# Run script and have fun


########################################################################################################################
# Imports
import pandas as pd
import praw

from matplotlib import pyplot as plt


########################################################################################################################
# API Setup / variables / settings

reddit = praw.Reddit(client_id='',
                     client_secret='',
                     user_agent='')

# Define the subreddit and the thread ID
subreddit_name = 'OMSCS'
thread_id = 'spbavt'

# Show all rows and columns in Pandas
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)


########################################################################################################################
# Functions

def find_between(s, first, last):
    try:
        start = s.index(first) + len(first)
        end = s.index(last, start)
        return s[start:end]
    except ValueError:
        return ""


########################################################################################################################
# Get Data

# Get the submission object for the thread
submission = reddit.submission(id=thread_id)

# Get all top-level comments and their replies
comments = submission.comments.list()

# Print all top-level comments and their replies
n = 0
dict_responses = {}
for comment in comments:
    try:
        # print(comment.body)
        s_application_date = find_between(s=comment.body, first='Application Date:** ', last='\n')
        s_decision_date = find_between(s=comment.body, first='Decision Date:** ', last='\n')
        s_status = find_between(s=comment.body, first='Status:** ', last='\n')
        # for reply in comment.replies:
        #     print('\t' + reply.body)
        if s_decision_date == '':
            continue
        else:
            dict_responses[n] = {'application_date': s_application_date, 'decision_date': s_decision_date, 'status': s_status}
    except AttributeError:
        continue
    n += 1


df = pd.DataFrame.from_dict(dict_responses, orient='index')


########################################################################################################################
# Clean up data

# Decision date (not the cleanest, but gets the job done)
replacements = \
    {'03': '3', '04': '4', '05': '5', '06': '6', '09': '9', 'May': '5', '\r': '', '\\\\': '', '<': '', '>': ''}
df['decision_date_cleaned1'] = df['decision_date'].replace(replacements, regex=True).str.strip()
# Take first part supplied
df['decision_date_cleaned2'] = df['decision_date_cleaned1'].apply(lambda x: x.split(' ')[0])
# One of clean up
df['decision_date_cleaned2'].replace('4/27', '4/27/2022', inplace=True)
df['decision_date_cleaned3'] = pd.to_datetime(df['decision_date_cleaned2'], errors='coerce')
df['decision_day'] = df['decision_date_cleaned3'].dt.day_name()
df['decision_dayofweek_number'] = df['decision_date_cleaned3'].dt.dayofweek
# Status
df['status_cleaned'] = df['status']\
    .replace({'\r': '', '\\': '', '<': '', '>': '', '[': '', ']': ''})\
    .str.strip()\
    .str.lower()\
    .apply(lambda x: x.split(' ')[0].replace('\\', '').replace('!', ''))
df['status_cleaned'] = df['status_cleaned'].str.replace(r'\[<(.+?)>\].*', r'\1', regex=True)
df['status_cleaned'].replace('', 'unknown', inplace=True)


########################################################################################################################
# Summarize and combine for graph

df_dates = pd.DataFrame(
    {'date_': pd.date_range(start=df['decision_date_cleaned3'].min(), end=df['decision_date_cleaned3'].max())})

df_counts = pd.DataFrame(df.groupby(by=['decision_date_cleaned3', 'decision_day']).size()).reset_index()
df_combined = pd.merge(left=df_dates, right=df_counts, left_on='date_', right_on='decision_date_cleaned3', how='left')
df_combined.rename(columns={0: 'responses'}, inplace=True)
df_combined.fillna(0, inplace=True)


########################################################################################################################
# Review

# Show plot
ax = df_combined.plot(
    x='date_',
    y='responses',
    kind='line',
    title='Number of OMSCS Responses by Day in 2022',
    xlabel='Date',
    ylabel='Number of Responses',
    figsize=(10, 5))
ax.get_figure().show()
# plt.show()
# ax.get_figure().savefig('decision_date_trend.png', format='png')

# Show day of week
df_dow = df.groupby(by=['decision_dayofweek_number', 'decision_day']).size().reset_index()
df_dow.rename(columns={0: 'responses'}, inplace=True)
n_responses = df_dow['responses'].sum()
df_dow['pct_of_total'] = df_dow.apply(lambda x: round(x['responses']/n_responses*100, 2), axis=1)
df_dow

# Review counts of statuses
df.groupby(by='status_cleaned').size()
