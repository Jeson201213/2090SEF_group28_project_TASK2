# 2090SEF_group28_project_TASK2

Backend 2 (data_service.py): Its core consists of SQLite data storage and Pandas report calculation. It provides basic CRUD operations and data backup, serving as the "data foundation" of the entire system.
Backend 1 (business_service.py): It encapsulates business interfaces based on FastAPI, adds business rules such as amount verification and account verification, and acts as an intermediate layer between the frontend and the data layer.
Frontend (frontend.py): A visual interface is quickly implemented using Streamlit, integrating line charts/pie charts to display reports, which can be used without frontend development experience.
