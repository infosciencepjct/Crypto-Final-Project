from calendar import c
from msilib.schema import Icon
from threading import local
import streamlit as st 
from streamlit_option_menu import option_menu
from streamlit_lottie import st_lottie
from datetime import date
import datetime
from PIL import Image
import pandas as pd
import yfinance as yf
from fbprophet import Prophet
from fbprophet.plot import plot_plotly
from plotly import graph_objs as go
import pickle
from pathlib import Path
import plotly.express as px
from dbfuncs import *

# - Settings and layouts -
lottie1 = load_lottieurl("https://assets7.lottiefiles.com/packages/lf20_0plko8zx.json")
lottie2 = load_lottieurl("https://assets10.lottiefiles.com/private_files/lf30_gonpfxdh.json")
st.set_page_config(page_title="SMS Crypto",page_icon=":chart_with_upwards_trend:")
  
# -- Main Menu --
image = Image.open('images/SMS_Crypto.png')
frs_clmn, scnd_clmn = st.columns((1,2))
with frs_clmn:
    st.write("")
with scnd_clmn:
    st.image(image, width=250)
selected_page = option_menu(
    menu_title = None,
    options = ["Home","Prediction","Blog","Transactions"],
    icons = ["house","graph-up-arrow","newspaper","coin"],
    menu_icon = "cast",
    default_index = 0,
    orientation = "horizontal",
    styles={"nav-link-selected":{"background-color":"#326da8"}}
)

# --- Home page ---
if selected_page == "Home":
    st.title("SMS Crypto")

    st.balloons()        
    left_clmn, right_clmn = st.columns(2)
    with right_clmn:
        st_lottie(lottie1, height=250, key="crypto")
    with left_clmn:
        st.subheader("Your place for Crypto currency Prediction and more!")
        st.write("Get crypto currency current state, future prediction, ")
        st. write("crypto posts on our blog - all in one place!")
    st.write("---")
    
    left_clmn, right_clmn = st.columns((1,2))
    with right_clmn:
        st.subheader("Manage your Crypto transactions in one place")
        st.write("You can track all your Crypto currency transactions -")
        st.write(" investments and sells, in all Crypto coins you'd like!")
    with left_clmn:
        st_lottie(lottie2, height=250, key="crypto2")
    st.write("---")
    
    left_clmn, right_clmn = st.columns(2)
    with right_clmn:
        st.image("images/blogpic.jpg")
    with left_clmn:
        st.subheader("Find out what's new in CryptoCurrency")
        st.write("Read all the latest new, get updates on what's")
        st.write("new in Crypto currency and Crypto market,")
        st.write("worldwide.")
    st.write("---")
    
    st.subheader(":mailbox: Do you have something to tell us?")
    st.write("You are more than welcome to leave a message, and we'll get back to you ASAP!")
    contact_form_layout="""
    <form action="https://formsubmit.co/infosciencefinalproject@gmail.com" method="POST">
        <input type="text" placeholder="Name" name="name" required>
        <input type="email" placeholder="Email" name="email" required>
        <textarea placeholder="Your message" name="message"</textarea>
        <button type="submit">Send</button>
    </form>
    """
    st.markdown(contact_form_layout, unsafe_allow_html=True)
    def use_css(filename):
        with open(filename) as f:
            st.markdown(f"<style>{f.read()}</style>",unsafe_allow_html=True)
    use_css("style.css")
# ---  End of Home page ---    

# --- Predictions page ----
elif selected_page =="Prediction":
    st.title("Crypto currency Prediction")
    start = "2019-01-01"
    today = date.today().strftime("%Y-%m-%d")
    coins = ("BTC-USD", "CRO-USD", "DOGE-USD", "ETH-USD","BNB-USD","MATIC-USD","ATOM-USD")

    st.sidebar.title("Filters")
    selected_coin = st.sidebar.selectbox("Select coin for Prediction", coins)

    st.sidebar.markdown(""":date:""", True)
    n_years = st.sidebar.selectbox("Select the time frame to predict:",["Tomorrow","Next Week","Next Month","In 3 Month"])
    if (n_years =="Tomorrow"):
        period = 1
    elif (n_years == "Next Week"):
        period = 7
    elif (n_years == "Next Month"):
        period = 30
    else:
        period = 90

    def load_data(currency):
        # Checking our database to determine our next action
        if(checkIfCollectionExists(currency)): 
            if(checkIfNeedUpdateDB(currency)):
                # if it does indeed need to be updated
                data=yf.download(currency,getLastDateFromDB(currency),today)
                updateMongoDB(data,currency)

                data = getMongoDBData(currency)
                data.reset_index(inplace=True)
                return data
            else:
                # if it doesnt need to be updated
                data = getMongoDBData(currency)
                data.reset_index(inplace=True)
                return data
        else:
            # if the collection doesnt exist, create a new one with new data
            data=yf.download(currency,start,today)
            updateMongoDB(data,currency)
            data.reset_index(inplace=True)
            return data

    data = load_data(selected_coin)

    with st.container():
        leftClmn, rightClm = st.columns((1,9))
        with leftClmn:
            if(selected_coin =="BTC-USD"):
                st.image('images/bitcoin.png', width=50)
            if(selected_coin =="ETH-USD"):
                st.image('images/ethereum.png', width=50)
            if(selected_coin =="DOGE-USD"):
                st.image('images/doge.png', width=50)
        with rightClm:
            st.subheader("Raw Data - " + selected_coin)

    st.write(data.tail())

    def plot_raw_data():
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=data['Date'], y =data['Open'], name='Coin_open'))
        fig.add_trace(go.Scatter(x=data['Date'], y =data['Close'], name='Coin_Close'))
        fig.layout.update(title_text="Time series Data", xaxis_rangeslider_visible=True)
        st.plotly_chart(fig)
        
    plot_raw_data()

    #Forecasting
    df_train= data[['Date','Close']]
    df_train = df_train.rename(columns={"Date":"ds","Close":"y"})

    m = Prophet()
    m.fit(df_train)
    future = m.make_future_dataframe(periods=period)
    forecast= m.predict(future)

    st.write("---")
    st.subheader('Forecast Data - '+ selected_coin)
    st.write(forecast.tail())

    fig1 = plot_plotly(m, forecast)
    st.plotly_chart(fig1)

    st.write('Forecast Compomnents')
    fig2 = m.plot_components(forecast)
    st.write(fig2)
# --- End of Predictions page ----

# --- Blog page ---
elif selected_page =="Blog":
    # - Settings and layouts for blog
    title_tmplt = """
    <a href="{}" target="_blank" style="text-decoration:none">
    <div style="border-radius:10px;padding:10px;margin:10px;border-style:solid;border-color:#326da8;">
    <h4>{}</h4>
    <h6>author: {}</h6>
    <h6>date: {}</h6>
    <br/>
    <p>{}</p>
    </div>
    </a>
    """
    st.title('Crypto Blog')
    # Create table if not exist
    create_table_blog()
    # Admin selection to show or add posts to blog 
    admin = st.sidebar.selectbox("Admin",["Show posts","Add posts"])
    if(admin == "Show posts"):
        all_posts = view_all_posts()
        for i in all_posts:
            title = i[0]
            author = i[1]
            article = i[2]
            pbdate = i[3]
            link = i[4]
            st.markdown(title_tmplt.format(link,title,author,pbdate,article),unsafe_allow_html=True)
    
    if(admin == "Add posts"):
        st.subheader("Add post to blog")
        ptitle = st.text_input("Post Title")
        pauthor = st.text_input("Author")
        particle = st.text_input("Article text")
        pdate = st.date_input("Date")
        link = st.text_input("Link")
        if st.button("Add"):
            add_post(ptitle,pauthor,particle,pdate,link)
            st.success("Post {} published". format(ptitle))
# --- End of Blog page ---        
    
# --- Transactions page ---
elif selected_page =="Transactions":
    st.title("My Transactions")
    menu=['Show All','Add', 'Edit', 'Delete']
    choice = st.sidebar.selectbox("Menu",menu)

    create_table()
    num = 0
    #Show all transactions
    if (choice == "Show All"):
        lst = selectall()
        df = pd.DataFrame(lst,columns=['Num','Transaction Type','Sum','Crypto Coin','Date','Note'])
        st.dataframe(df)
      #Pie chart for coins transaction amount
        coinslst = selectallCoins()
        df = pd.DataFrame(coinslst)
        fig = px.pie(df,names=0,values=1,title="Transactions distribution",labels={"0":"Coin ","1":"Amount "}, hole= 0.3)
        st.plotly_chart(fig)

    #Add a new investment
    elif (choice == "Add"):
        st.subheader("Add a transaction")
        right_clmn, left_clmn = st.columns(2)
        with right_clmn:
            tran_type=st.selectbox("Transaction Type",["Investment","Sell"])
            tran_sum = st.number_input("Sum of transaction",min_value =0)
            tran_coin = st.selectbox("Transaction coin",["BTC-USD", "CRO-USD", "DOGE-USD", "ETH-USD","BNB-USD","MATIC-USD","ATOM-USD"])
        with left_clmn:
            tran_date = st.date_input("Date")
            tran_note = st.text_area("Notes")
            lsttran = getlastnum()
            if (lsttran):
                lstnum = [i[0] for i in lsttran]
                num = lstnum[0]+1
            else:
                num = 1
        if st.button("Add Transaction"):
            add_transaction(num,tran_type,tran_sum,tran_coin,tran_date,tran_note)
            st.success("Successfully added transaction number: {}".format(num, tran_sum))
            with st.expander("See all transactions"):
                lst = selectall()
                df = pd.DataFrame(lst,columns=['Num','Transaction Type','Sum','Crypto Coin','Date','Note'])
                st.dataframe(df)
        
    #Update a transaction     
    elif (choice == "Edit"):
        st.subheader("Edit transaction")
        with st.expander("See all transactions"):
            lst = selectall()
            df = pd.DataFrame(lst,columns=['Num','Transaction Type','Sum','Crypto Coin','Date','Note'])
            st.dataframe(df)
        list_of_nums = [i[0] for i in selectall()]
        select_tran = st.selectbox("Transaction to Edit",list_of_nums)
        numselected = get_transaction(select_tran)
        st.write('---')
        
        #Update selected num
        if(numselected):
            tnum = numselected[0][0]
            ttype = numselected[0][1]
            tsum =  numselected[0][2]
            tcoin =  numselected[0][3]
            tdate =  numselected[0][4]
            tnote=  numselected[0][5]
            
            if tnum>0:
                right_clmn, left_clmn = st.columns(2)
                with right_clmn:
                    if ttype == "Investment":
                        nwtran_type=st.selectbox("Transaction Type",["Investment","Sell"], index=0)
                    else:
                        nwtran_type=st.selectbox("Transaction Type",["Investment","Sell"], index=1)
                        
                    nwtran_sum = st.number_input("Sum of transaction",value = tsum,min_value =0)
                    
                    # Present on select box the coin from the chosen transaction
                    if tcoin =="BTC-USD":
                        nwtran_coin = st.selectbox("Transaction coin",["BTC-USD", "CRO-USD", "DOGE-USD", "ETH-USD","BNB-USD","MATIC-USD","ATOM-USD"], index=0)
                    if tcoin =="CRO-USD":
                        nwtran_coin = st.selectbox("Transaction coin",["BTC-USD", "CRO-USD", "DOGE-USD", "ETH-USD","BNB-USD","MATIC-USD","ATOM-USD"], index=1)
                    elif tcoin =="DOGE-USD":
                        nwtran_coin = st.selectbox("Transaction coin",["BTC-USD", "CRO-USD", "DOGE-USD", "ETH-USD","BNB-USD","MATIC-USD","ATOM-USD"], index=2)
                    elif tcoin =="ETH-USD":
                        nwtran_coin = st.selectbox("Transaction coin",["BTC-USD", "CRO-USD", "DOGE-USD", "ETH-USD","BNB-USD","MATIC-USD","ATOM-USD"], index=3)
                    elif tcoin =="BNB-USD":
                        nwtran_coin = st.selectbox("Transaction coin",["BTC-USD", "CRO-USD", "DOGE-USD", "ETH-USD","BNB-USD","MATIC-USD","ATOM-USD"], index=4)
                    elif tcoin =="MATIC-USD":
                        nwtran_coin = st.selectbox("Transaction coin",["BTC-USD", "CRO-USD", "DOGE-USD", "ETH-USD","BNB-USD","MATIC-USD","ATOM-USD"], index=5)
                    elif tcoin =="ATOM-USD":
                        nwtran_coin = st.selectbox("Transaction coin",["BTC-USD", "CRO-USD", "DOGE-USD", "ETH-USD","BNB-USD","MATIC-USD","ATOM-USD"], index=6)
                    
                with left_clmn:
                    trimdate = tdate.split("-")
                    year = trimdate[0][2]+trimdate[0][3]
                    trdate = trimdate[2]+"/"+trimdate[1]+"/"+year
                    tnwdate = datetime.datetime.strptime(trdate, '%d/%m/%y')
                    nwtran_date = st.date_input("Date", value=tnwdate)
                    
                    nwtran_note = st.text_area("Notes",tnote)
            else:
                st.warning("You Have no transactions or you need to select one from the list")   
                
            if st.button("Update Transaction"):
                update_tran(nwtran_type,nwtran_sum,nwtran_coin,nwtran_date,nwtran_note,tnum)
                st.success("Successfully updated transaction number: {}".format(tnum))
                lst2 = selectall()
                # present the updated transaction
                df2 = pd.DataFrame(lst2,columns=['Num','Transaction Type','Sum','Crypto Coin','Date','Note'])
                with st.expander("Updated transactions"):
                    st.dataframe(df2)
        
    # Delete an investment     
    elif (choice =="Delete"):
        st.subheader("Delete transaction")
        st.write(num)
        with st.expander("See all transactions"):
            lst = selectall()
            df = pd.DataFrame(lst,columns=['Num','Transaction Type','Sum','Crypto Coin','Date','Note'])
            st.dataframe(df)
        list_of_nums = [i[0] for i in selectall()]
        select_tran = st.selectbox("Transaction to Delete",list_of_nums)
        numselected = get_transaction(select_tran)
        tnum = numselected[0][0]
        st.warning("Are you sure you want to delete the transaction {}?".format(tnum))
        if st.button("Delete"):
            delete_tran(tnum)
            st.success("Successfully deleted transaction number: {}".format(tnum))
# --- End of Transactions page ---