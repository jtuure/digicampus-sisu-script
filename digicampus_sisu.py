"""Makes a Sisu report based on the Digicampus.fi report and Sisu list of enrolled students for faster registering of the ECTS

Author:
    Juuso Tuure  - 31.10.2024
"""

import pandas as pd
import numpy as np
import codecs
from itertools import permutations

#  Load data
df = pd.read_csv('digicampus_example.csv')  # From Digicampus report
doc = codecs.open('sisu_example.csv', encoding="utf-8") # From Sisu enrollments. You might need to switch between "utf-8" and "utf-16" if not working.
df2 = pd.read_csv(doc, sep='\t')


# Function to generate all possible name combinations from firstnames + lastname
def generate_name_combinations(row):
    first_names = row['ETUNIMET'].split()
    last_name = row['SUKUNIMI']
    
    # Generate all possible combinations of first names (with 1 to len(first_names))
    combinations = []
    for r in range(1, len(first_names) + 1):
        for combo in permutations(first_names, r):
            full_name = f"{' '.join(combo)} {last_name}"
            combinations.append(full_name)
    return combinations


# Fill in number of credits, grade and language of the course
credits = 3
grade = 'Hyv.'
language = 'Suomi'


# Remove unnecessary columns (the last column contains status of the course)
columns_to_keep = list(df.columns[:3]) + [df.columns[-1]]

# Keep only the selected columns
df = df[columns_to_keep]

# Remove rows where the 4th column is empty (The student has not completed the course yet)
df = df[df.iloc[:, 3].notna()]

# List to store sutdent emails that are not from "@helsinki.fi"
non_helsinki_names = []

# Loop through the email column and check the condition
for i in range(len(df)):
    if not(df['Sähköpostiosoite'].iloc[i].endswith('@helsinki.fi')):
        non_helsinki_names.append(df['Nimi'].iloc[i])

# Collect all matching names
matching_names = []

# Loop through the DataFrame rows
for index, row in df2.iterrows():
    possible_names = generate_name_combinations(row)
    
    # Check if any generated name is in the name_list
    for name in possible_names:
        if name in non_helsinki_names:
            matching_names.append((name,index))
            
            
# Generate columns needed for the report
df['firstName (optional)'] = ''
df['lastName (optional)'] = ''
df['studentNumber'] = ''
df['grade'] = ''
df['credits'] = '' 
df['completionLanguage'] = ''
df['comment'] = ''
df['transcriptinfo-fi'] = ''
df['transcriptinfo-sv'] = ''
df['transcriptinfo-en'] = ''

# IF a student with a @helsinki.fi email in digicampus has completed.
for i in range(len(df)):
    for j in range(len(df2)):
        if (df['Sähköpostiosoite'].iloc[i] == df2['ENSISIJAINEN SÄHKÖPOSTI'].iloc[j]):
            df['firstName (optional)'].iloc[i] = df2['ETUNIMET'].iloc[j]
            df['lastName (optional)'].iloc[i] = df2['SUKUNIMI'].iloc[j]
            df['studentNumber'].iloc[i] = df2['OPISKELIJANUMERO'].iloc[j]
            df['grade'].iloc[i] = grade
            df['credits'].iloc[i] = credits
            df['completionLanguage'].iloc[i] = language         
            
            
# IF a student with a some else email in digicampus has completed.
    for k in range(len(matching_names)):
        if (df['Nimi'].iloc[i] == matching_names[k][0]):
            df['firstName (optional)'].iloc[i] = df2['ETUNIMET'].iloc[matching_names[k][1]]
            df['lastName (optional)'].iloc[i] = df2['SUKUNIMI'].iloc[matching_names[k][1]]
            df['studentNumber'].iloc[i] = df2['OPISKELIJANUMERO'].iloc[matching_names[k][1]]
            df['grade'].iloc[i] = grade
            df['credits'].iloc[i] = credits
            df['completionLanguage'].iloc[i] = language
              

# Format the assessment date to a string and re-name the column
df['assessmentDate'] = pd.to_datetime(df['Kurssi suoritettu'].str.split(',').str[0], dayfirst=True, errors='coerce').dt.strftime('%d.%m.%Y')                
df['studentNumber'] = '0' + df['studentNumber'].astype(str)  # Add zero to the student number         
df = df.sort_values('lastName (optional)') # Sort according to the lastnames

   
# Make a list of students who have completed the course but are not enrolled to the course in Sisu
not_enrolled_df = df[df['firstName (optional)'].isnull() | (df['firstName (optional)'] == '')]
not_enrolled_df = not_enrolled_df.drop(columns=not_enrolled_df.loc[:, 'firstName (optional)':].columns) #Drop empty columns

# Drop unnecessary columns and rows from the report
df = df.drop(df.loc[:, 'ID':'Kurssi suoritettu'].columns, axis=1)
df['grade'].replace('', np.nan, inplace=True)
df.dropna(subset=['grade'], inplace=True)

# Make the ordrer of columns right
col = df.pop('assessmentDate')  # Remove and store the column as col
df.insert(5, 'assessmentDate', col)  # Insert it at proper index


# Write the SIMU (Sisu muunnin/Sisu coverter) applicable output file as .csv (columns delimited with semicolon)
df.to_csv('upload_to_SISU.csv', index=False, sep=';', header=True)

# Write a .csv file of the students who have completed the course in Digicampus, but not enrolled in Sisu
not_enrolled_df.to_csv('list_of_not_enrolled.csv', index=False, sep=',', header=True)


