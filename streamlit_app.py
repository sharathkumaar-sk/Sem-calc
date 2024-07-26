import streamlit as st
import pdfplumber
import pandas as pd

def extract_data_from_pdf(file_path):
    try:
        with pdfplumber.open(file_path) as pdf:
            page = pdf.pages[0]
            table = page.extract_table()
            df = pd.DataFrame(table[1:], columns=table[0])
            return df
    except Exception as e:
        st.error(f"An error occurred: {e}")
        return None

def process_data(df):
    if "Subject Code" in df.columns and "Total" in df.columns and "Result" in df.columns:
        df = df[["Subject Code", "Total", "Result"]]
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
    st.title("Semester mark calculator")
    file_paths = st.file_uploader("Upload your PDF files (one for each semester)", type=["pdf"], accept_multiple_files=True)
    if file_paths:
        semester_results = []
        overall_total_marks = 0
        overall_total_maximum_marks = 0
        for i, file_path in enumerate(file_paths):
            df = extract_data_from_pdf(file_path)
            if df is not None:
                result_df, total_marks, percentage, cgpa, maximum_marks = process_data(df)
                semester_results.append((result_df, total_marks, percentage, cgpa, maximum_marks))
                overall_total_marks += total_marks
                overall_total_maximum_marks += maximum_marks
        if semester_results:
            for i, (result_df, total_marks, percentage, cgpa, maximum_marks) in enumerate(semester_results):
                st.title(f"Semester {i+1} Results:")
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
