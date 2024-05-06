# LabClass

## 1. Setup Miniconda
**Download and Install Miniconda**
- Download Miniconda from [Miniconda Website](https://docs.anaconda.com/free/miniconda/)
- Follow installation instructions for your operating system.
- Once installed, open the Miniconda Command Prompt. (Click Windows Key and Type Anaconda Prompt.)
### 1.2 Create Conda Python Environment
> conda create --name your_env_name python=3.9
### 1.3 Activate Conda Python Environment
> conda activate your_env_name
## 2. Setup FastAPI
### 2.1 Install FastAPI, Uvicorn, and MySQL Connector
- pip install fastapi uvicorn mysql-connector-python
- pip install bcrypt
- pip install python-multipart
### 2.2 Run FastAPI
> uvicorn main:app --reload

## 3. Setup Database
- Download the recent Database SQL file
- Open your XAMPP, and click 'Start' for Apache and and MySQL
- Create a database named **labclass** then import the downloaded SQL file

## 4. Setup FastAPI Routers for Table Users
### 4.1 Select Interpreter
- Open your VS Code
- Install the Python extension (if not installed yet)
- Click 'ctrl + shift + P' then search for Python
- Click 'Select Interpreter'
- Choose the one with your virtual environment's name
### 4.2 Clone GitHub Repository
> git clone [https://github.com/AshleyRiannaMorales/LabClass_BE.git](https://github.com/AshleyRiannaMorales/LabClass_BE.git)
## 5. Test the FastAPI Routers
### 5.1 Run FastAPI
> uvicorn main:app --reload
### 5.2 Open FastAPI Docs in Browser
> Visit http://127.0.0.1:8000/docs
  
 
