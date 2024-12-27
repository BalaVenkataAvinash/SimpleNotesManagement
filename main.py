from flask import Flask,request,render_template,redirect,url_for,flash,session,send_file
import mysql.connector #for connecting database it is one of the package for connecting database
#from mysql.connector import (connection)
from otp import genotp
from cmail import sendmail
from stoken import encode,decode
from flask_session import Session
from io import BytesIO

admin={'useremail':'admin','password':'admin'}

app=Flask(__name__) # these is called object creation
app.config['SESSION_TYPE']='filesystem'
app.secret_key='otp'
#mydb=connection.MysqlConnection(user='root',password='admin',host='localhost',database='snmproject')

Session(app)

mydb=mysql.connector.connect(host='localhost',user='root',password='Admin',db='snmproject')

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register',methods=['GET','POST'])
def register():
    if request.method=='POST':
        print(request.form)
        username=request.form['username']
        uemail=request.form['email']
        password=request.form['password']
        cpassword=request.form['cpassword']
        if password!=cpassword:
            flash('Password and confirm password should Match')
            return redirect(url_for('register'))
        cursor=mydb.cursor()
        cursor.execute('select count(useremail) from users where useremail=%s',[uemail])
        result=cursor.fetchone()
        print(result)
        if result[0]==0:
            gotp=genotp()
            print(gotp)
            udata={'username':username,'uemail':uemail,'pword':password,'otp':gotp}
            subject='OTP for Simple Notes Manager'
            body=f'otp for registration of simple notes manager {gotp}'
            sendmail(to=uemail,subject=subject,body=body)
            flash('OTP has sent to given Mail.')
            return redirect(url_for('otp',enudata=encode(data=udata)))
        elif result[0]>0:
            flash('Email already existed')
        else:
            return 'Somthing Went Wrong'
    return render_template('register.html')

@app.route('/otp/<enudata>',methods=['GET','POST'])
def otp(enudata):
    if request.method=='POST':
        uotp=request.form['otp']
        try:
            dudata=decode(data=enudata) #udata={'username':username,'uemail':uemail,'pword':password,'otp':gotp}
        except Exception as e:
            print(e)
            return "something went wrong"
        else:
            if dudata['otp']==uotp:
                cursor=mydb.cursor()
                cursor.execute('insert into users(username,useremail,password) values(%s,%s,%s)',[dudata['username'],dudata['uemail'],dudata['pword']])
                mydb.commit()
                cursor.close()
                flash('Registration completed successfully')
                return redirect(url_for('login'))
            else:
                return 'otp was wrong pls register again'
    return render_template('otp.html')

@app.route('/login',methods=['GET','POST'])
def login():
    if request.method=='POST':
        uemail=request.form['email']
        pword=request.form['password']
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select count(useremail) from users where useremail=%s',[uemail])
        bdata=cursor.fetchone()
        if bdata[0]==1:
            cursor.execute('select password from users where useremail=%s',[uemail])
            bpassword=cursor.fetchone()
            if pword==bpassword[0].decode('utf-8'):
                print(session)
                session['user'] = uemail
                print(session)
                return redirect(url_for('dashboard'))
            else:
                flash('Pasword was Wrong')
                return redirect(url_for('login'))
        elif bdata[0]==0:
            flash('Email not existed')
            return redirect(url_for('register'))
        else:
            return 'Something went wrong'
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/addnotes',methods=['GET','POST'])
def addnotes():
    if request.method=='POST':
        title=request.form['title']
        description=request.form['description']
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select userid from users where useremail=%s',[session.get('user')])
        uid=cursor.fetchone()
        if uid:
            try:
                cursor.execute('insert into notes(title,ndescription,userid) values(%s,%s,%s)',[title,description,uid[0]])
                mydb.commit()
                cursor.close()
                
            except Exception as e:
                print(e)
                flash('Duplicate Title Entry')
                return redirect(url_for('addnotes'))
            else:
                flash('Notes Added Successfully')
                return redirect(url_for('dashboard'))
        else:
            return 'Something Went Wrong'
    return render_template('addnotes.html')

@app.route('/view_all_notes')
def view_all_notes():
    cursor=mydb.cursor(buffered=True)
    cursor.execute('select userid from users where useremail=%s',[session.get('user')])
    uid=cursor.fetchone()
    cursor.execute('select nid,title,create_at from notes where userid=%s',[uid[0]])
    ndata=cursor.fetchall()  # iwill return in tuple format of all data   data from backend be like [(1,"python"),(2,"java")]
    return render_template('view_all_notes.html',ndata=ndata)

@app.route('/viewnotes/<nid>')
def viewnotes(nid):
    cursor=mydb.cursor(buffered=True)
    cursor.execute('select * from notes where nid=%s',[nid])
    ndata=cursor.fetchone() #(1,"python","hellowrold")
    return render_template('viewnotes.html',ndata=ndata)

@app.route('/updatenotes/<nid>',methods=['GET','POST'])
def updatenotes(nid):
    cursor=mydb.cursor(buffered=True)
    cursor.execute('select * from notes where nid=%s',[nid])
    ndata=cursor.fetchone()
    if request.method=='POST':
        title=request.form['title']
        description=request.form['description']
        cursor=mydb.cursor(buffered=True)
        cursor.execute('update notes set title=%s,ndescription=%s where nid=%s',[title,description,nid])
        mydb.commit()
        cursor.close()
        flash('Notes Updated Successfully')
        return redirect(url_for('viewnotes',nid=nid))
    return render_template('updatenotes.html',ndata=ndata)

@app.route('/delete/<nid>')
def delete(nid):
    try:
        cursor=mydb.cursor(buffered=True)
        cursor.execute('delete from notes where nid=%s',[nid])
        mydb.commit()
        cursor.close()
    except Exception as e:
        print(e)
        flash('could not delete notes')
    else:
        flash('notes deleted succesfully')
        return redirect(url_for('view_all_notes'))

@app.route('/uplodefile',methods=['GET','POST'])
def uplodefile():
    if request.method=='POST':
        filedata=request.files['file']
        # print(filedata)
        # print(filedata.read())
        fname=filedata.filename
        fdata=filedata.read()
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select userid from users where useremail=%s',[session.get('user')])
            uid=cursor.fetchone()
            cursor.execute('insert into filedata(filename,fdata,added_by) values(%s,%s,%s)',[fname,fdata,uid[0]])
            mydb.commit()
        except Exception as e:
            print(e)
            flash('could not uplode the file')
            return redirect(url_for('dashboard'))
        else:
            flash('file uploded succesfully')
            return redirect(url_for('dashboard'))
    return render_template('uplodefile.html')

@app.route('/viewallfiles')
def viewallfiles():
    try:
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select userid from users where useremail=%s',[session.get('user')])
        uid=cursor.fetchone()
        cursor.execute('select fid,filename,created_at from filedata where added_by=%s',[uid[0]])
        fdata=cursor.fetchall() 
        print(fdata)
    except Exception as e:
        print(e)
        flash('no data found')
        return redirect(url_for('dashboard'))
    else:
        return render_template('viewallfiles.html',fdata=fdata)
    
@app.route('/viewfile/<nid>')
def viewfile(nid):
    try:
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select filename,fdata from filedata where fid=%s',[nid])
        fdata=cursor.fetchone() # (1,python,'jhgvb',2024-12-14 12:37:18)
        bytes_data=BytesIO(fdata[1])
        return send_file(bytes_data,download_name=fdata[0],as_attachment=False)
    except Exception as e:
        print(e)
        flash('cannot open file')
        return redirect(url_for('dashboard'))
    
@app.route('/downloadfile/<nid>')
def downloadfile(nid):
    try:
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select filename,fdata from filedata where fid=%s',[nid])
        fdata=cursor.fetchone() # (1,python,'jhgvb',2024-12-14 12:37:18)
        bytes_data=BytesIO(fdata[1])
        return send_file(bytes_data,download_name=fdata[0],as_attachment=True)
    except Exception as e:
        print(e)
        flash('cannot open file')
        return redirect(url_for('dashboard'))
    
@app.route('/deletefile/<nid>')
def deletefile(nid):
    try:
        cursor=mydb.cursor(buffered=True)
        cursor.execute('delete from filedata where fid=%s',[nid])
        mydb.commit()
        cursor.close()
    except Exception as e:
        print(e)
        flash('could not delete file')
        return redirect(url_for('viewallfiles'))
    else:
        flash('file deleted succesfully')
        return redirect(url_for('viewallfiles'))

@app.route('/logout')
def logout():
    if session.get('user'):
        session.pop('user')
        return redirect(url_for('home'))
    else:
        return redirect(url_for('login'))

app.run(debug=True)




#git remote add origin https://github.com/BalaVenkataAvinash/Simple-Notes-Management.git
#git branch -M main
#git push -u origin main