import streamlit as st
import pdfplumber
import pandas as pd
import re
from dateutil import parser
from datetime import datetime

# Define SEMESTER_MAPPING
SEMESTER_MAPPING = {
    datetime(2022, 3, 25): 'Semester 1',
    datetime(2022, 9, 1): 'Semester 2',
    datetime(2023, 3, 21): 'Semester 3',
    datetime(2023, 9, 15): 'Semester 4',
    datetime(2024, 3, 29): 'Semester 5',
    datetime(2024, 7, 26): 'Semester 6'
}

# Define the subject codes for which marks need to be calculated
PREDEFINED_SUBJECTS = ['SE211','SE21A','SM3AA','SM3AE','SU221','SU22A','SZ231','SZ23A','SZ23B','SZ23C','SZ33A','ENV4B','SZ241','SZ24A','SZ24B','SZ24C','SZ34A','SE251','SE252','SE25B','SE25C','SU25A','SU45B','NMU46','SU46B','SZ261','SZ26A','SZ26B','SZ26C','SZ26Q']  # Replace with your actual subject codes

# Function to extract text from PDF and find dates
def extract_data_from_pdf(file_path):
    try:
        with pdfplumber.open(file_path) as pdf:
            page = pdf.pages[0]
            text = page.extract_text()
            table = page.extract_table()
            df = pd.DataFrame(table[1:], columns=table[0])
            dates = extract_dates(text)
            return df, dates
    except Exception as e:
        st.error(f"An error occurred: {e}")
        return None, None

# Function to normalize dates
def normalize_date(date_str):
    try:
        # Remove ordinal suffixes
        date_str = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', date_str)
        # Parse date using dateutil.parser
        return parser.parse(date_str).strftime('%d-%m-%Y')
    except ValueError:
        return None

# Function to convert date string to datetime object
def string_to_datetime(date_str):
    try:
        return parser.parse(date_str)
    except ValueError:
        return None

# Function to map a date to the semester
def map_date_to_semester(date_str):
    date_obj = string_to_datetime(date_str)
    if date_obj:
        closest_date = min(SEMESTER_MAPPING.keys(), key=lambda d: abs(d - date_obj))
        return SEMESTER_MAPPING.get(closest_date, 'Unknown Semester')
    return 'Unknown Semester'

# Function to extract dates using regex
def extract_dates(text):
    # Regex to find various date formats
    date_patterns = [
        r'\d{1,2}[-/]\d{1,2}[-/]\d{4}',        # e.g., 01-04-2022
        r'\d{1,2}[st|nd|rd|th] [A-Za-z]+[-/]\d{4}',  # e.g., 1st April-2022
        r'[A-Za-z]+ \d{1,2}, \d{4}',            # e.g., April 1, 2022
    ]
    dates = []
    for pattern in date_patterns:
        for match in re.finditer(pattern, text):
            normalized_date = normalize_date(match.group())
            if normalized_date:
                dates.append(normalized_date)
    return dates

# Function to process data for selected subjects
def process_data(df, selected_subjects):
    if "Subject Code" in df.columns and "Total" in df.columns and "Result" in df.columns:
        df = df[["Subject Code", "Total", "Result"]]
        df = df[df["Subject Code"].isin(selected_subjects)]  # Filter by predefined subjects
        df["Total"] = pd.to_numeric(df["Total"], errors='coerce')
        df = df.dropna(subset=["Total"])
        total_marks = df["Total"].sum()
        num_subjects = len(df)
        maximum_marks = num_subjects * 100
        percentage = (total_marks / maximum_marks) * 100
        cgpa = percentage / 9.5
        return df, total_marks, percentage, cgpa, maximum_marks
    else:
        st.error("The required columns are not present in the DataFrame.")
        return None, None, None, None, None

def main():
    st.title("Semester Mark Calculator")
    
    # File uploader
    file_paths = st.file_uploader("Upload your PDF files (one for each semester)", type=["pdf"], accept_multiple_files=True)
    
    if file_paths:
        semester_results = []
        semester_dates = []
        overall_total_marks = 0
        overall_total_maximum_marks = 0
        
        # Iterate through each file
        for i, file_path in enumerate(file_paths):
            df, dates = extract_data_from_pdf(file_path)
            
            if df is not None:
                # Use predefined subjects
                selected_subjects = PREDEFINED_SUBJECTS
                
                result_df, total_marks, percentage, cgpa, maximum_marks = process_data(df, selected_subjects)
                semester_results.append((result_df, total_marks, percentage, cgpa, maximum_marks))
                if dates:
                    mapped_semester = map_date_to_semester(dates[0])
                    semester_dates.append(mapped_semester)
                else:
                    semester_dates.append('Unknown Semester')
                overall_total_marks += total_marks
                overall_total_maximum_marks += maximum_marks
        
        if semester_results:
            for i, (result_df, total_marks, percentage, cgpa, maximum_marks) in enumerate(semester_results):
                st.title(f"{semester_dates[i]} Results:")
                styles = [
                    dict(selector="th", props=[("text-align", "center")]),
                    dict(selector="td", props=[("text-align", "center")]),
                    dict(selector=".col0", props=[("width", "150px")]),
                    dict(selector=".col1", props=[("width", "150px")]),
                    dict(selector=".col2", props=[("width", "150px")]),
                ]
                html = result_df.style.set_table_styles(styles).to_html(index=False)
                st.write(html, unsafe_allow_html=True)
                st.write(f"Total Marks: {total_marks} / {maximum_marks}")
                st.write(f"Percentage: {percentage:.2f}%")
                st.write(f"CGPA: {cgpa:.2f}")
                st.write("\n")
            overall_cgpa = sum(cgpa for _, _, _, cgpa, _ in semester_results) / len(semester_results)
            overall_percentage = (overall_total_marks / overall_total_maximum_marks) * 100
            st.title(f"Overall Total Marks: {overall_total_marks} / {overall_total_maximum_marks}")
            st.title(f"Overall Percentage: {overall_percentage:.2f}%")
            st.title(f"Overall CGPA: {overall_cgpa:.2f}")

if __name__ == "__main__":
    main()
