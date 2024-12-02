# Project Links and Resources

## Looker Studio
- **[Dashboard](https://lookerstudio.google.com/reporting/510fc2fb-d8b9-4d67-b9b1-d7a88eec16b0/page/p_3q8w7by2md/edit)**  
This interactive dashboard in Looker Studio provides real-time visualizations and metrics related to the IoT data. It aggregates insights from the database and logs, offering analytics on performance, decrypted metrics, and sensor data trends for informed decision-making.

## Firestore
- **[Database](https://console.firebase.google.com/project/iotagri-3f696/firestore/databases/-default-/data/~2Fapple)**  
Firestore is used to store structured IoT data, including sensor readings and device configurations. This link takes you to the collection and documents, allowing you to manage and query your IoT data efficiently.

## Source Code
- **[Cloud Run Source Code](https://console.cloud.google.com/run/detail/asia-south1/decryptdatalatestmodified/source?inv=1&invt=Abh2xw&project=iotagri-3f696)**  
This section contains the source code deployed on Cloud Run. The service handles decryption of sensor data and other processing tasks in a serverless environment, ensuring scalability and performance for IoT workloads.

## Log Data
- **[BigQuery Logs](https://console.cloud.google.com/bigquery?referrer=search&inv=1&invt=Abh3tw&project=iotagri-3f696&ws=!1m33!1m3!3m2!1siotagri-3f696!2sDATA_PREPARATION!1m4!4m3!1siotagri-3f696!2sDATA_PREPARATION!3slogs_table!1m3!3m2!1siotagri-3f696!2sLogData!1m4!1m3!1siotagri-3f696!2sbquxjob_353d653c_1934287b2ca!3sasia-south1!1m4!4m3!1siotagri-3f696!2sLogData!3sdecrypted_combined_metrics_view!1m4!1m3!1siotagri-3f696!2sbquxjob_f5ed7b_19344d238bd!3sasia-south1!1m4!4m3!1siotagri-3f696!2sLogData!3srun_googleapis_com_stderr_20241119!1m5!1m4!1m3!1siotagri-3f696!2sbquxjob_1e8f503_1934299c8dc!3sasia-south1)**  
BigQuery serves as the centralized repository for log data, including both raw and processed logs. This link allows you to explore datasets and metrics, enabling debugging and advanced analytics for IoT data pipelines.

## Cloud Run Triggers
- **[Triggers](https://console.cloud.google.com/run/detail/asia-south1/decryptdatalatestmodified/triggers?inv=1&invt=Abh2xw&project=iotagri-3f696)**  
This page provides an overview of Cloud Run triggers set up for the project. These triggers ensure automatic execution of the decryption service in response to Firestore events or other triggers, streamlining the data pipeline.

## BigQuery
- **[BigQuery Console](https://console.cloud.google.com/bigquery?project=iotagri-3f696&ws=!1m9!1m3!3m2!1siotagri-3f696!2sLog_Data!1m4!4m3!1siotagri-3f696!2sLogData!3sexported_logs&inv=1&invt=Abh3pw)**  
BigQuery provides an interactive SQL-based environment for querying IoT log data. This link allows you to explore exported logs, perform analytics, and derive insights from the encrypted and decrypted datasets.

## IAM Management
- **[IAM Console](https://console.cloud.google.com/iam-admin/iam?referrer=search&inv=1&invt=Abh04A&project=iotagri-3f696)**  
The IAM console is where you manage permissions and roles for users and services within the project. Use this link to ensure secure access control and proper resource management across the IoT platform.