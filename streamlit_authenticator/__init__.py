import os
import jwt
import bcrypt
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
import extra_streamlit_components as stx
import streamlit.components.v1 as components

_RELEASE = True

class hasher:
    def __init__(self,passwords):
        """Create a new instance of "hasher".
        Parameters
        ----------
        passwords: list
            The list of plain text passwords to be hashed.
        Returns
        -------
        list
            The list of hashed passwords.
        """
        self.passwords = passwords

    def hash(self,password):
        """
        Parameters
        ----------
        password: str
            The plain text password to be hashed.
        Returns
        -------
        str
            The hashed password.
        """
        self.password = password
        return bcrypt.hashpw(self.password.encode(), bcrypt.gensalt()).decode()

    def generate(self):
        """
        Returns
        -------
        list
            The list of hashed passwords.
        """
        self.hashedpw = []

        for password in self.passwords:
            self.hashedpw.append(self.hash(password))
        return self.hashedpw

class authenticate:
    def __init__(self,names,usernames,passwords,cookie_name,key,cookie_expiry_days=30):
        """Create a new instance of "authenticate".
        Parameters
        ----------
        names: list
            The list of names of users.
        usernames: list
            The list of usernames in the same order as names.
        passwords: list
            The list of hashed passwords in the same order as names.
        cookie_name: str
            The name of the JWT cookie stored on the client's browser for passwordless reauthentication.
        key: str
            The key to be used for hashing the signature of the JWT cookie.
        cookie_expiry_days: int
            The number of days before the cookie expires on the client's browser.
        Returns
        -------
        str
            Name of authenticated user.
        boolean
            The status of authentication, None: no credentials entered, False: incorrect credentials, True: correct credentials.
        """
        self.names = names
        self.usernames = usernames
        self.passwords = passwords
        self.cookie_name = cookie_name
        self.key = key
        self.cookie_expiry_days = cookie_expiry_days

    def token_encode(self):
        """
        Returns
        -------
        str
            The JWT cookie for passwordless reauthentication.
        """
        return jwt.encode({'name':st.session_state['name_var'],
        'exp_date':self.exp_date},self.key,algorithm='HS256')

    def token_decode(self):
        """
        Returns
        -------
        str
            The decoded JWT cookie for passwordless reauthentication.
        """
        return jwt.decode(self.token,self.key,algorithms=['HS256'])

    def exp_date(self):
        """
        Returns
        -------
        str
            The JWT cookie's expiry timestamp in Unix epoch.
        """
        return (datetime.utcnow() + timedelta(days=self.cookie_expiry_days)).timestamp()

    def check_pw(self):
        """
        Returns
        -------
        Boolean
            The validation state for the input password by comparing it to the hashed password on disk.
        """
        return bcrypt.checkpw(self.password_var.encode(),self.passwords[self.index].encode())

    def login(self,form_name,location='main'):
        """Create a new instance of "authenticate".
        Parameters
        ----------
        form_name: str
            The rendered name of the login form.
        location: str
            The location of the login form i.e. main or sidebar.
        Returns
        -------
        str
            Name of authenticated user.
        boolean
            The status of authentication, None: no credentials entered, False: incorrect credentials, True: correct credentials.
        """
        self.location = location
        self.form_name = form_name

        if self.location not in ['main','sidebar']:
            raise ValueError("Location must be one of 'main' or 'sidebar'")

        cookie_manager = stx.CookieManager()

        if 'authenticated' not in st.session_state:
            st.session_state['authenticated'] = None
        if 'name_var' not in st.session_state:
            st.session_state['name_var'] = None

        if st.session_state['authenticated'] != True:
            try:
                self.token = cookie_manager.get(self.cookie_name)
                self.token = self.token_decode()

                if self.token['exp_date'] > datetime.utcnow().timestamp():
                    st.session_state['name_var'] = self.token['name']
                    st.session_state['authenticated'] = True
                else:
                    st.session_state['authenticated'] = None
            except:
                st.session_state['authenticated'] = None

            if st.session_state['authenticated'] != True:
                if self.location == 'main':
                    login_form = st.form('Login')
                elif self.location == 'sidebar':
                    login_form = st.sidebar.form('Login')

                login_form.subheader(self.form_name)
                self.username_var = login_form.text_input('Username')
                self.password_var = login_form.text_input('Password',type='password')

                if login_form.form_submit_button('Login'):
                    self.index = None
                    for i in range(0,len(self.usernames)):
                        if self.usernames[i] == self.username_var:
                            self.index = i
                    if self.index != None:
                        try:
                            if self.check_pw():
                                st.session_state['name_var'] = self.names[self.index]
                                self.exp_date = self.exp_date()
                                self.token = self.token_encode()
                                cookie_manager.set(self.cookie_name, self.token)
                                st.session_state['authenticated'] = True
                            else:
                                st.session_state['authenticated'] = False
                        except:
                            raise ValueError("Please enter hashed passwords and not plain text passwords into the 'authenticate' module.")
                    else:
                        st.session_state['authenticated'] = False

        if st.session_state['authenticated'] == True:
            if self.location == 'main':
                if st.button('Logout'):
                    cookie_manager.delete(self.cookie_name)
                    st.session_state['name_var'] = None
                    st.session_state['authenticated'] = None
            elif self.location == 'sidebar':
                if st.sidebar.button('Logout'):
                    cookie_manager.delete(self.cookie_name)
                    st.session_state['name_var'] = None
                    st.session_state['authenticated'] = None

        return st.session_state['name_var'], st.session_state['authenticated']

if not _RELEASE:
    names = ['John Smith','Rebecca Briggs']
    usernames = ['jsmith','rbriggs']
    passwords = ['123','456']

    hashed_passwords = hasher(passwords).generate()

    authenticator = authenticate(names,usernames,hashed_passwords,'streamlit_authenticator','123456',cookie_expiry_days=30)
    name, authentication_status = authenticator.login('Login','main')

    if authentication_status:
        st.write('Welcome *%s*' % (name))
    elif authentication_status == False:
        st.error('Username/password is incorrect')
    elif authentication_status == None:
        st.warning('Please enter your username and password')