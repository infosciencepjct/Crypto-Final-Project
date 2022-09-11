import sqlite3
from urllib import request
from streamlit_lottie import st_lottie
import requests
import datetime
import pandas as pd

def load_lottieurl(url):
    req = requests.get(url)
    if req.status_code != 200:
        return None
    return req.json()

def get_MongoDatabase():
    from pymongo import MongoClient
    ## Provide the mongodb atlas url to connect python to mongodb using pymongo
    ## Ignore the following line, used to connect to the database on website but cannot make it work for some reason
    #CONNECTION_STRING = "mongodb+srv://Maris:qrweafsd@finalproject.j3pn0.mongodb.net/shop?retryWrites=true&w=majority"

    ## Connects to our local storage
    ##CONNECTION_STRING = "mongodb://localhost:27017/"
    CONNECTION_STRING ="mongodb+srv://Maris:qrweafsd@finalproject.j3pn0.mongodb.net/myFirstDatabase?retryWrites=true&w=majority"

    ## Create a connection using MongoClient. You can import MongoClient or use pymongo.MongoClient
    client = MongoClient(CONNECTION_STRING)

    ## Create the database
    return client['siteData']

def turnDateToStr(String):
    #just a placeholder for our conversion
    resolvedString = ""
    #loops through the String we got and fetching our only the numbers into our new resolvedString variable
    for m in String:
        if m.isdigit():
            resolvedString = resolvedString + m
    return resolvedString

def checkIfCollectionExists(currency):
    #retrieving access to mongoDB
    mongoDB = get_MongoDatabase()
    #getting all of our collection names in ["siteData"] (which we acceessed to from previous command)
    listOfMongoDBCollection = mongoDB.list_collection_names()
    for collection in listOfMongoDBCollection:
        #Check if there is an existing collection
        if(currency == collection):
            return True
    return False
def getLastDateFromDB(currency):
    #retrieving access to mongoDB
    mongoDB = get_MongoDatabase()
    #finding our last date in the corresponding currency collection and warping in list for easy access
    lastDoc = list(mongoDB[currency].find().sort('Date',-1).limit(1))
    #return only the date attribute
    return lastDoc[0]["Date"]

def checkIfNeedUpdateDB(currency):
    #get the current day time
    currentDay = datetime.datetime.now()
    #we use this function to retrieve the last document in our database based on the currency the user has selected
    docDate = getLastDateFromDB(currency)

    #convert the string to date format
    dateString = docDate + " 23:59:59"
    format = "%Y-%m-%d %H:%M:%S"
    docDate = datetime.datetime.strptime(dateString, format)

    #checking if there is a gap between the current day time and the last document from our selected currency
    if(currentDay - datetime.timedelta(days = 1) > docDate):
        return True
    else:
        return False

def createMongoDataTable(dataAcquired, fromDatabase):
    # since the data format we get from yfinance is a bit different from the data format from our mongoDB
    # need to specify from where it came
    if(fromDatabase):
        # Building our own table, first we extend the length of the table by the length of our dataAcquired(original data) with the desired columns
        data = pd.DataFrame(index=range(0,len(dataAcquired)),columns=["Date","High","Low","Open","Close","Volume","Adj Close"])
        # Then we simply copy paste the data from "dataAcquired" to "data" with this simple for loop
        for i in range(0,len(data)):
            data["Date"][i]=dataAcquired[i]["Date"]
            data["High"][i]=dataAcquired[i]["High"]
            data["Low"][i]=dataAcquired[i]["Low"]
            data["Open"][i]=dataAcquired[i]["Open"]
            data["Close"][i]=dataAcquired[i]["Close"]
            data["Volume"][i]=dataAcquired[i]["Volume"]
            data["Adj Close"][i]=dataAcquired[i]["Adj Close"]
        # Convert object date to date format (if our lowest price had $ or anything else, it would have been an object too so we would have needed to convert it aswell)
        data["Date"] = pd.to_datetime(data.Date, format="%Y-%m-%d %H:%M:%S").dt.date
        data = data.astype({
            "High": float,
            "Low": float,
            "Open": float,
            "Close": float,
            "Volume": float,
            "Adj Close": float
        })
        return data
    else:
        # Building our own table, first we extend the length of the table by the length of our dataAcquired(original data) with the desired columns
        data = pd.DataFrame(index=range(0,len(dataAcquired)),columns=["Date","High","Low","Open","Close","Volume","Adj Close"])
        # Then we simply copy paste the data from "dataAcquired" to "data" with this simple for loop
        for i in range(0,len(data)):
            data["Date"][i]=dataAcquired.index[i]
            data["High"][i]=dataAcquired["High"][i]
            data["Low"][i]=dataAcquired["Low"][i]
            data["Open"][i]=dataAcquired["Open"][i]
            data["Close"][i]=dataAcquired["Close"][i]
            data["Volume"][i]=dataAcquired["Volume"][i]
            data["Adj Close"][i]=dataAcquired["Adj Close"][i]
        # Convert object date to date format (if our lowest price had $ or anything else, it would have been an object too so we would have needed to convert it aswell)
        data["Date"] = pd.to_datetime(data.Date, format="%Y-%m-%d %H:%M:%S").dt.date
        data = data.astype({
            "High": float,
            "Low": float,
            "Open": float,
            "Close": float,
            "Volume": float,
            "Adj Close": float
        })
        return data
def updateMongoDB(dataFetched, currency):
    #retrieving access to mongoDB
    mongoDB = get_MongoDatabase()

    #creating our own table for the data we get from yahoo finance
    data = createMongoDataTable(dataFetched,False)
    # iterating through the data, and each row we put into our database
    numC = 0
    for row in range(0,len(data)):
        id = turnDateToStr(str(data.iloc[row]["Date"]))
        date = id[:4]+"-"+id[4:6]+"-"+id[6:]
        oneRow = {
        "_id" : id,
        "Date": date,
        "Currency" : currency,
        "High": data.iloc[row]["High"],
        "Low": data.iloc[row]["Low"],
        "Open": data.iloc[row]["Open"],
        "Close": data.iloc[row]["Close"],
        "Volume": data.iloc[row]["Volume"],
        "Adj Close": data.iloc[row]["Adj Close"]
        }
        # we have this section to eliminate to possibility of inserting an already existing document (date cannot repeat itself)
        exist = False
        for doc in list(mongoDB[currency].find({"_id":id})):
            if(doc):
                exist = True
        if(exist):

            print("Already added row number: ", numC)
        else:
            mongoDB[currency].insert_one(oneRow)
            print("Added row number: ", numC)
        numC = numC + 1

def getMongoDBData(currency):
    # connect to mongoDB and return ALL the data for the current currency we want to display as a list
    # we use list because the data cannot be accessed without it
    # True refers to if it came from database for the createTable
    mongoDB = get_MongoDatabase()
    return createMongoDataTable(list(mongoDB[currency].find()),True)

# --- sqlite3 functions for Blog page ---
def connection():
    conn = sqlite3.connect("blogposts.db",check_same_thread=False)
    c = conn.cursor()
    return conn, c

def create_table_blog():
    conn, c = connection()
    c.execute('CREATE TABLE IF NOT EXISTS posts(title TEXT, author TEXT ,post_text TEXT, pubdate DATE, link TEXT)')
    conn.commit()
    conn.close()    
    
def add_post(title,author,post_text,pubdate,link):
    conn, c = connection()
    c.execute('INSERT INTO posts(title, author, post_text,pubdate,link) VALUES (?,?,?,?,?)',(title,author,post_text,pubdate,link))
    conn.commit()
    conn.close()
    
def view_all_posts():
    conn, c = connection()
    c.execute('SELECT * FROM posts ORDER BY pubdate DESC')
    allposts = c.fetchall()
    conn.commit()
    conn.close()    
    return allposts

def dropBlog():
    conn, c = connection()
    c.execute('DROP TABLE posts')
    conn.commit()
    conn.close()
    
    
# --- Sqlite3 functions for Transactions page ---
def connection():
    conn = sqlite3.connect("transactions.db",check_same_thread=False)
    c = conn.cursor()
    return conn, c
     
def create_table():
    conn, c = connection()
    c.execute('CREATE TABLE IF NOT EXISTS transactions(num NUMBER, tran_type TEXT, tran_sum NUMBER ,tran_coin TEXT, tran_date DATE, tran_note TEXT)')
    conn.commit()
    conn.close()

def getlastnum():
    conn,c = connection()
    c.execute('SELECT * FROM transactions ORDER BY num DESC LIMIT 1')
    lsttran = c.fetchall()
    conn.commit()
    conn.close()
    return lsttran
    
def add_transaction(num,tran_type,tran_sum,tran_coin,tran_date,tran_note):
    conn, c = connection()
    c.execute('INSERT INTO transactions(num,tran_type,tran_sum,tran_coin,tran_date,tran_note) VALUES(?,?,?,?,?,?)',(num,tran_type,tran_sum,tran_coin,tran_date,tran_note))
    conn.commit()
    conn.close()
    
def selectall():
    conn, c = connection()
    c.execute('SELECT * FROM transactions')
    lst = c.fetchall()
    conn.commit()
    conn.close()
    return lst

def selectallCoins():
    conn, c = connection()
    c.execute('SELECT tran_coin, COUNT(*) FROM transactions GROUP BY tran_coin')
    lst = c.fetchall()
    conn.commit()
    conn.close()
    return lst

def get_transaction(tran_num):
    conn, c = connection()
    c.execute('SELECT * FROM transactions WHERE num="{}"'.format(tran_num))
    tran = c.fetchall()
    conn.commit()
    conn.close()
    return tran

def update_tran(nwtran_type,nwtran_sum,nwtran_coin,nwtran_date,nwtran_note,num):
    conn, c = connection()
    c.execute("UPDATE transactions SET tran_type=?,tran_sum=?,tran_coin=?,tran_date=?,tran_note=? WHERE num=?",(nwtran_type,nwtran_sum,nwtran_coin,nwtran_date,nwtran_note,num))
    conn.commit()
    tran = c.fetchall()
    conn.close()
    return tran

def delete_tran(num):
    conn, c = connection()
    c.execute("DELETE FROM transactions WHERE num=?",(num,))
    conn.commit()
    conn.close()

def drop():
    conn, c = connection()
    c.execute('DROP TABLE transactions')
    conn.commit()
    conn.close()