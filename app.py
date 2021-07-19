import json
from numbers import Number
import pdfkit
import simplejson, decimal
from datetime import date
from decimal import Decimal
from random import randint
import MySQLdb
import MySQLdb.cursors
from decimal import Decimal
from flask import Flask, render_template, url_for, session, request, flash, redirect, jsonify, make_response
from flask_mysqldb import MySQL
from forms import LoginForm, BrandForm, ProductForm, SaleForm, CategoryForm, RefundForm, VendorForm, ProductSearchForm, \
    SaleOrderSearchForm, RefundOrderSearchForm, StoreForm, POSForm, WarehouseForm, GRPOForm, GRPOSearchForm, \
    CustomerForm, CustomerSearchForm, StoreSearchForm, InventorySearchForm, VendorSearchForm, BrandSearchForm, \
    WarehouseSearchForm, CategorySearchForm, POSSearchForm, GoodsReceiptForm, GoodsIssueForm, GoodsReceiptSearchForm, \
    GoodsIssueSearchForm, DailySaleReportForm

app = Flask(__name__)

app.config['MYSQL_HOST']='digitalpos.mysql.pythonanywhere-services.com'
app.config['MYSQL_DATABASE_PORT'] = int(3306),
app.config['MYSQL_USER']='digitalpos'
app.config['MYSQL_PASSWORD']='Lahore@123'
app.config['MYSQL_DB']='digitalpos$pos'


# app.config['MYSQL_HOST']='localhost'
# app.config['MYSQL_DATABASE_PORT'] = int(3306),
# app.config['MYSQL_USER']='root'
# app.config['MYSQL_PASSWORD']='Lahore@123'
# app.config['MYSQL_DB']='pos'


mysql = MySQL(app)
app.secret_key = '\xfd{H\xe5<\x95\xf9\xe3\x96.5\xd1\x01O<!\xd5\xa2\xa0\x9fR"\xa1\xa8'

@app.route('/', methods=['GET','POST'])
def main():
    if 'usersessionid' in session:
        return render_template('index.html')
    else:
        return redirect (url_for('login'))


@app.route('/index')
def index():
    if 'usersessionid' in session:
        return render_template('index.html')
    else:
        return redirect (url_for('login'))



@app.route('/login', methods=['GET', 'POST'])
def login():
    myloginform=LoginForm(request.form)
    if request.method=='GET':
        cursor = mysql.connection.cursor()
        cursor.execute("select storekey, storename from store union all select 0, 'Select Store' order by storekey ")
        allstore = cursor.fetchall()
        myloginform.storename.choices = allstore
        cursor.execute("select poskey, posname from pos union all select 0, 'Select POS' order by poskey ")
        allpos = cursor.fetchall()
        myloginform.posname.choices = allpos
        cursor.close()

    if request.method=='POST':
        username =  request.form['username']
        userpassword = request.form['userpassword']
        storekey = request.form['storename']
        poskey= request.form['posname']
        cursor = mysql.connection.cursor(cursorclass=MySQLdb.cursors.DictCursor)
        sqlst="""select * from user 
        left join userstore on user.userkey=userstore.userkey
        left join store on userstore.storekey=store.storekey
        left join pos on userstore.poskey=pos.poskey
        where username = (%s) and userpassword = (%s) 
        and store.storekey=%s and pos.poskey=%s
        """
        values = [(username), (userpassword) ,  (storekey), (poskey)]
        # print (values)
        cursor.execute(sqlst, values)
        userdata=cursor.fetchall()
        if (userdata):
            session['usersessionid']=randint(1000, 100000)
            session['userkey']=userdata[0]['userkey']
            session['storekey']=userdata[0]['storekey']
            session['poskey']=userdata[0]['poskey']
            session['warehousekey'] = getwarehousekey(userdata[0]['storekey'])
            session['username'] = userdata[0]['username']
            session['storename'] = userdata[0]['storename']
            session['posname'] = userdata[0]['posname']
            cursor.close()
            return render_template('index.html')
        else:
            flash('Invalid login details')
            return redirect(url_for('login'))
    else:
        return render_template('/login.html', form=myloginform)



class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return str(o)
        return super(DecimalEncoder, self).default(o)


def getwarehousekey(storekey):
    sqlst="select warehousekey from store where storekey=%s"
    values = [(storekey)]
    cursor=mysql.connection.cursor()
    cursor.execute(sqlst, values)
    warehousekey = cursor.fetchall()
    return warehousekey




@app.route('/brand', methods=['GET','POST'])
def brand():
    myform = BrandForm(request.form)
    if 'usersessionid' in session:
        if request.method=='POST':
            # Process Form
            brandid = request.form['brandid']
            brandname= request.form['brandname']
            cursor = mysql.connection.cursor()
            cursor.execute("insert into brand (brandid, brandname) values (%s, %s) " ,  ([brandid] , [brandname]))
            mysql.connection.commit()
            cursor.close()
            flash( 'Brand Added')
            return redirect(url_for('brand'))
        else:
            return render_template('accounts/brand.html', form=myform)
    else:
        return redirect (url_for('login'))




@app.route('/store', methods=['GET','POST'])
def store():
    mystoreform = StoreForm(request.form)
    cursor = mysql.connection.cursor()
    cursor.execute("select warehousekey, warehouseid from warehouse union all select 0, 'Select Warehouse' order by warehousekey ")
    allwarehouses = cursor.fetchall()
    mystoreform.warehousename.choices = allwarehouses

    cursor.execute(
        "select customerkey, customername from customer union all select 0, 'Select Customer' order by customerkey ")
    allcustomers = cursor.fetchall()
    mystoreform.defaultcustomername.choices = allcustomers


    if 'usersessionid' in session:
        if mystoreform.validate_on_submit():
            if request.method=='POST':
                # Process Form
                storename= request.form['storename']
                storeid = request.form['storeid']
                warehousekey=request.form['warehousename']
                defaultcustomerkey = request.form['defaultcustomername']
                cursor = mysql.connection.cursor()
                sqlst="insert into store (storeid ,storename, warehousekey, defaultcustomerkey) values (%s, %s, %s,  %s) "
                values=[ (storeid), (storename),(warehousekey), (defaultcustomerkey)]
                cursor.execute(sqlst ,values)
                mysql.connection.commit()
                cursor.close()
                flash( 'Store Added')
                return redirect(url_for('store'))
            else:
                return render_template('accounts/store.html', form=mystoreform)
        else:
            return render_template('accounts/store.html', form=mystoreform)
    else:
        return redirect (url_for('login'))



@app.route('/pos', methods=['GET','POST'])
def pos():
    myposform = POSForm(request.form)
    cursor = mysql.connection.cursor()
    cursor.execute("select storekey, storeid from store union all select 0, 'Select Store' order by storekey ")
    allstores = cursor.fetchall()
    myposform.storename.choices = allstores
    if 'usersessionid' in session:
        if myposform.validate_on_submit():
            if request.method=='POST':
                # Process Form
                storename= request.form['storename']
                posid = request.form['posid']
                posname=request.form['posname']
                cursor = mysql.connection.cursor()
                sqlst="insert into pos (posid ,posname, storekey) values (%s, %s, %s) "
                values=[ (posid), (posname) , (storename)]
                cursor.execute(sqlst ,values)
                mysql.connection.commit()
                cursor.close()
                flash( 'POS Added')
                return redirect(url_for('pos'))
            else:
                return render_template('accounts/pos.html', form=myposform)
        else:
            return render_template('accounts/pos.html', form=myposform)
    else:
        return redirect (url_for('login'))


@app.route('/warehouse', methods=['GET','POST'])
def warehouse():
    mywarehouseform = WarehouseForm(request.form)
    cursor = mysql.connection.cursor()
    cursor.execute("select warehousekey, warehouseid from warehouse union all select 0, 'Select Warehouse' order by warehouseid ")
    allwarehouses = cursor.fetchall()
    mywarehouseform.warehousename.choices = allwarehouses
    if 'usersessionid' in session:
        if request.method=='POST':
            # Process Form
            warehousename= request.form['warehousename']
            warehouseid = request.form['warehouseid']

            cursor = mysql.connection.cursor()
            sqlst="insert into warehouse (warehouseid ,warehousename) values (%s, %s) "
            values=[(warehouseid), (warehousename)]
            cursor.execute(sqlst ,values)
            mysql.connection.commit()
            cursor.close()
            flash( 'Warehouse Added')
            return redirect(url_for('store'))
        else:
            return render_template('accounts/warehouse.html', form=mywarehouseform)
    else:
        return redirect (url_for('login'))




@app.route('/category', methods=['GET','POST'])
def category():
    mycategoryform = CategoryForm(request.form)
    if 'usersessionid' in session:
        if request.method=='POST':
            # Process Form
            categoryid = request.form['categoryid']
            categoryname= request.form['categoryname']

            cursor = mysql.connection.cursor()
            cursor.execute("insert into category (categoryid ,categoryname) values (%s,%s) " ,  ([categoryid], [categoryname]))
            mysql.connection.commit()
            cursor.close()
            flash( 'Category Added')
            return redirect(url_for('category'))
        else:
            return render_template('accounts/category.html', form=mycategoryform)
    else:
        return redirect (url_for('login'))




@app.route('/vendor', methods=['GET','POST'])
def vendor():
    myvendorform = VendorForm(request.form)
    if 'usersessionid' in session:
        if request.method=='POST':
            # Process Form
            vendorid = request.form['vendorid']
            vendorname= request.form['vendorname']
            cursor = mysql.connection.cursor()
            cursor.execute("insert into vendor (vendorid, vendorname) values (%s, %s) " ,  ([vendorid],[vendorname]))
            mysql.connection.commit()
            cursor.close()
            flash( 'Vendor Added')
            return redirect(url_for('vendor'))
        else:
            return render_template('accounts/vendor.html', form=myvendorform)
    else:
        return redirect (url_for('login'))




@app.route('/product', methods=['GET','POST'])
def product():
    myproductform = ProductForm(request.form)

    cursor = mysql.connection.cursor()
    cursor.execute("select brandkey, brandname from brand union all select 0, 'Select Brand' order by brandkey ")
    allbrands=cursor.fetchall()
    myproductform.brandname.choices = allbrands

    cursor.execute("select vendorkey, vendorname from vendor union all select 0, 'Select Vendor' order by vendorkey ")
    allvendors = cursor.fetchall()
    myproductform.vendorname.choices = allvendors

    cursor.execute("select categorykey, categoryname from category union all select 0, 'Select Category' order by categorykey ")
    allcategories = cursor.fetchall()
    myproductform.categoryname.choices = allcategories

    if 'usersessionid' in session:

        if myproductform.validate_on_submit():
            if request.method=='POST':
                # Process Form
                usersessionid=session['usersessionid']
                productid = request.form['productid']
                productname=request.form['productname']
                brandkey= request.form['brandname']
                categorykey = request.form['categoryname']
                vendorkey = request.form['vendorname']
                saleprice = request.form['saleprice']
                barcode = request.form['barcode']

                cursor = mysql.connection.cursor()
                sqlst="""insert into product (usersessionid , productid , productname, brandkey, categorykey, vendorkey, saleprice, barcode) 
                values (%s,%s, %s, %s, %s,%s,%s,%s)"""
                values = [(usersessionid), (productid) , (productname), (brandkey), (categorykey), (vendorkey), (saleprice), (barcode)]
                cursor.execute(sqlst, values)

                # get latest product key
                sqlst = "select productkey from product where usersessionid=%s and productkey=(select LAST_INSERT_ID())"
                myvalues = [(usersessionid)]
                cursor.execute(sqlst, myvalues)
                productkey = cursor.fetchall()

                # add product to all warehouses
                sqlst="""select warehousekey from warehouse"""
                cursor.execute(sqlst)
                recs=cursor.rowcount
                warehouselist=cursor.fetchall()

                for i in range(recs):
                    sqlst = "insert into inventory (productkey, warehousekey, onhandquantity) values (%s, %s, 0)"
                    values=[(productkey), (warehouselist[i][0])]
                    cursor.execute(sqlst, values)

                mysql.connection.commit()
                cursor.close()
                flash( 'Product Added')
                return redirect(url_for('product'))
            else:
                return render_template('accounts/product.html', form=myproductform)
        else:
            return render_template('accounts/product.html', form=myproductform)
    else:
        return redirect (url_for('login'))





@app.route('/customer', methods=['GET','POST'])
def customer():
    mycustomerform = CustomerForm(request.form)

    if 'usersessionid' in session:
        if mycustomerform.validate_on_submit():
            if request.method=='POST':
                # Process Form
                usersessionid=session['usersessionid']
                customerid = request.form['customerid']
                customername=request.form['customername']

                cursor = mysql.connection.cursor()
                sqlst="""insert into customer (usersessionid , customerid , customername) 
                values (%s, %s , %s )"""
                values = [usersessionid, (customerid) , (customername)]
                cursor.execute(sqlst, values)

                mysql.connection.commit()
                cursor.close()
                flash( 'Customer Added')
                return redirect(url_for('customer'))
            else:
                return render_template('accounts/customer.html', form=mycustomerform)
        else:
            return render_template('accounts/customer.html', form=mycustomerform)
    else:
        return redirect (url_for('login'))




@app.route('/updateproduct', methods=['GET','POST'])
def updateproduct():
    if 'usersessionid' in session:
            if request.method=='POST':
                # Process Form
                productid = request.form['productid']
                productname=request.form['productname']
                brandkey= request.form['brandname']
                categorykey = request.form['categoryname']
                vendorkey = request.form['vendorname']
                saleprice = request.form['saleprice']
                barcode = request.form['barcode']
                productkey = request.form['productkey']

                cursor = mysql.connection.cursor()
                sqlst="""update product set productid=%s,  productname=%s, brandkey=%s, categorykey=%s, vendorkey=%s, barcode=%s , saleprice=%s 
                where productkey=%s
                """
                values=[ (productid), (productname), (brandkey), (categorykey), (vendorkey), (barcode), (saleprice), (productkey)]

                cursor.execute(sqlst, values)
                mysql.connection.commit()
                cursor.close()
                return ( 'Product Updated')
    else:
        return redirect (url_for('login'))




@app.route('/updatecustomer', methods=['GET','POST'])
def updatecustomer():
    if 'usersessionid' in session:
            if request.method=='POST':
                # Process Form
                customerkey=request.form['customerkey']
                customerid = request.form['customerid']
                customername= request.form['customername']

                cursor = mysql.connection.cursor()
                sqlst="""update customer set customername=%s, customerid=%s
                where customerkey=%s
                """
                values=[(customername), (customerid), (customerkey)]
                # print (values)

                cursor.execute(sqlst, values)
                mysql.connection.commit()
                cursor.close()
                return ( 'Customer Updated')
    else:
        return redirect (url_for('login'))





@app.route('/updatepos', methods=['GET','POST'])
def updatepos():
    if 'usersessionid' in session:
            if request.method=='POST':
                # Process Form
                poskey=request.form['poskey']
                posid = request.form['posid']
                posname= request.form['posname']
                storekey = request.form['store']

                cursor = mysql.connection.cursor()
                sqlst="""update pos set posname=%s, posid=%s, storekey=%s
                where poskey=%s
                """
                values=[(posname), (posid), (storekey) , (poskey)]
                # print (values)

                cursor.execute(sqlst, values)
                mysql.connection.commit()
                cursor.close()
                return ( 'POS Updated')
    else:
        return redirect (url_for('login'))






@app.route('/updatecategory', methods=['GET','POST'])
def updatecategory():
    if 'usersessionid' in session:
            if request.method=='POST':
                # Process Form
                categorykey=request.form['categorykey']
                categoryid = request.form['categoryid']
                categoryname= request.form['categoryname']

                cursor = mysql.connection.cursor()
                sqlst="""update category set categoryname=%s, categoryid=%s
                where categorykey=%s
                """
                values=[(categoryname), (categoryid), (categorykey)]
                # print (values)

                cursor.execute(sqlst, values)
                mysql.connection.commit()
                cursor.close()
                return ( 'Category Updated')
    else:
        return redirect (url_for('login'))







@app.route('/updatewarehouse', methods=['GET','POST'])
def updatewarehouse():
    if 'usersessionid' in session:
            if request.method=='POST':
                # Process Form
                warehousekey=request.form['warehousekey']
                warehouseid = request.form['warehouseid']
                warehousename= request.form['warehousename']

                cursor = mysql.connection.cursor()
                sqlst="""update warehouse set warehousename=%s, warehouseid=%s
                where warehousekey=%s
                """
                values=[(warehousename), (warehouseid), (warehousekey)]
                # print (values)

                cursor.execute(sqlst, values)
                mysql.connection.commit()
                cursor.close()
                return ( 'Warehouse Updated')
    else:
        return redirect (url_for('login'))








@app.route('/updatevendor', methods=['GET','POST'])
def updatevendor():
    if 'usersessionid' in session:
            if request.method=='POST':
                # Process Form
                vendorkey=request.form['vendorkey']
                vendorid = request.form['vendorid']
                vendorname= request.form['vendorname']

                cursor = mysql.connection.cursor()
                sqlst="""update vendor set vendorname=%s, vendorid=%s
                where vendorkey=%s
                """
                values=[(vendorname), (vendorid), (vendorkey)]
                print (values)

                cursor.execute(sqlst, values)
                mysql.connection.commit()
                cursor.close()
                return ( 'Vendor Updated')
    else:
        return redirect (url_for('login'))





@app.route('/updatebrand', methods=['GET','POST'])
def updatebrand():
    if 'usersessionid' in session:
            if request.method=='POST':
                # Process Form
                brandkey=request.form['brandkey']
                brandid = request.form['brandid']
                brandname= request.form['brandname']

                cursor = mysql.connection.cursor()
                sqlst="""update brand set brandname=%s, brandid=%s
                where brandkey=%s
                """
                values=[(brandname), (brandid), (brandkey)]

                cursor.execute(sqlst, values)
                mysql.connection.commit()
                cursor.close()
                return ( 'Brand Updated')
    else:
        return redirect (url_for('login'))






@app.route('/updatestore', methods=['GET','POST'])
def updatestore():
    if 'usersessionid' in session:
            if request.method=='POST':
                # Process Form
                storekey=request.form['storekey']
                storeid = request.form['storeid']
                storename= request.form['storename']
                warehouse = request.form['warehouse']
                defaultcustomername = request.form['defaultcustomername']

                cursor = mysql.connection.cursor()
                sqlst="""update store set storename=%s, storeid=%s, warehousekey=%s, defaultcustomerkey=%s
                where storekey=%s
                """
                values=[(storename), (storeid), (warehouse), (defaultcustomername), (storekey)]


                cursor.execute(sqlst, values)
                mysql.connection.commit()
                cursor.close()
                return ( 'Store Updated')
    else:
        return redirect (url_for('login'))






@app.route('/getinventory', methods=['GET','POST'])
def getinventory():
    if 'usersessionid' in session:
        if request.method=='POST':
            barcode= request.form['barcode']
            cursor = mysql.connection.cursor()
            sqlst="""select onhandquantity from product left join inventory on product.productkey=inventory.productkey 
            where barcode=%s and  warehousekey= %s """
            values = [(barcode), (session['warehousekey'])]
            cursor.execute(sqlst , values )
            onhandquantity=cursor.fetchall()
            # cursor.close()
            return  jsonify(onhandquantity)

    else:
        return redirect (url_for('login'))



@app.route('/grpo', methods=['GET', 'POST'])
def grpo():
    mygrpoform=GRPOForm(request.form)
    cursor=mysql.connection.cursor()
    sqlst="select vendorkey, vendorname from vendor union all select 0, 'Select Vendor' order by vendorkey"
    cursor.execute(sqlst)
    allvendors = cursor.fetchall()
    mygrpoform.vendorname.choices = allvendors

    sqlst="select warehousekey, warehousename from warehouse union all select 0, 'Select Warehouse' order by warehousekey"
    cursor.execute(sqlst)
    allwarehouses = cursor.fetchall()
    mygrpoform.warehousename.choices = allwarehouses

    if 'usersessionid' in session:
        if request.method=='POST':
            grpototal =  request.form['grandtotal']
            vendorkey=request.form['vendorkey']
            orderdate= request.form['orderdate']
            receiptdate = request.form['receiptdate']
            warehousekey=request.form['warehousekey']
            status=request.form['warehousekey']
            # print (request.form)
            list = [(k, v) for k, v in dict.items(request.form)]
            # print (list)
            productslist = list[0][1]
            chunks = [productslist[x:x+5] for x in range (0,len(productslist),5)]

            usersessionid=session['usersessionid']
            sqlst = """insert into grpo ( grpototal ,  usersessionid, userkey, 
            vendorkey, orderdate, receiptdate, warehousekey, status) values (%s, %s, %s, %s, %s, %s, %s, %s)"""

            myvalues=[(grpototal), (usersessionid), (session['userkey']), (vendorkey), (orderdate), (receiptdate), (warehousekey), (status)]
            cursor=mysql.connection.cursor()
            cursor.execute(sqlst, myvalues)


            sqlst="select grpokey from grpo where usersessionid=%s and grpokey=(select LAST_INSERT_ID())"
            myvalues=[(usersessionid)]
            cursor.execute(sqlst, myvalues)
            grpokey=cursor.fetchall()
            # print (saleorderkey)

            for row in chunks:
                # print (row)
                # get productkey
                # print (row[0])
                sqlst="select productkey from product where barcode=%s"
                myvalues=[(row[0])]
                cursor.execute(sqlst, myvalues)
                productkey = cursor.fetchall()
                barcode=row[0]
                productname=row[1]
                purchaseprice=row[2]
                quantity = row[3]
                linetotal=row[4]


                sqlst="""insert into grpodetail (grpokey, productkey, purchaseprice, quantity, linetotal,
                 productname, barcode, warehousekey) values (%s, %s,%s,%s,%s,%s,%s, %s )"""
                myvalues=[(grpokey), (productkey), (purchaseprice), (quantity), (linetotal), (productname), (barcode), (warehousekey) ]
                cursor.execute(sqlst, myvalues)

                # get existing qty
                sqlst="""select onhandquantity from inventory where productkey=%s and warehousekey=%s"""
                values=[(productkey), (warehousekey)]
                cursor.execute(sqlst, values)
                qtydata =cursor.fetchall()
                if (qtydata):
                    updatedquantity=(int(qtydata[0][0]) + int(quantity))
                    # update qty
                    sqlst="""update inventory set onhandquantity=%s where productkey=%s and warehousekey=%s"""
                    values=[ (updatedquantity) , (productkey), (warehousekey)]
                    cursor.execute(sqlst, values)
                else:
                    grpokey=0
                    print ('Product does not exist in Inventory table')
                    mysql.connection.rollback()

            mysql.connection.commit()

            return jsonify(grpokey)
        else:
            return render_template('accounts/grpomanual.html', form=mygrpoform)
    else:
        return redirect (url_for('login'))






@app.route('/goodsreceipt', methods=['GET', 'POST'])
def goodsreceipt():
    mygoodsreceiptform=GoodsReceiptForm(request.form)
    cursor=mysql.connection.cursor()

    sqlst="select warehousekey, warehousename from warehouse union all select 0, 'Select Warehouse' order by warehousekey"
    cursor.execute(sqlst)
    allwarehouses = cursor.fetchall()
    mygoodsreceiptform.warehousename.choices = allwarehouses

    if 'usersessionid' in session:
        if request.method=='POST':
            goodsreceipttotal =  request.form['grandtotal']
            receiptdate = request.form['receiptdate']
            warehousekey=request.form['warehousekey']
            reason=request.form['reason']
            # print (request.form)
            list = [(k, v) for k, v in dict.items(request.form)]
            # print (list)
            productslist = list[0][1]
            chunks = [productslist[x:x+5] for x in range (0,len(productslist),5)]

            usersessionid=session['usersessionid']
            sqlst = """insert into goodsreceipt ( goodsreceipttotal ,  usersessionid, userkey, 
            receiptdate, warehousekey, reason) values (%s, %s, %s, %s, %s, %s)"""

            myvalues=[(goodsreceipttotal), (usersessionid), (session['userkey']),  (receiptdate), (warehousekey), (reason)]
            cursor=mysql.connection.cursor()
            cursor.execute(sqlst, myvalues)


            sqlst="select goodsreceiptkey from goodsreceipt where usersessionid=%s and goodsreceiptkey=(select LAST_INSERT_ID())"
            myvalues=[(usersessionid)]
            cursor.execute(sqlst, myvalues)
            goodsreceiptkey=cursor.fetchall()
            # print (saleorderkey)

            for row in chunks:
                # print (row)
                # get productkey
                # print (row[0])
                sqlst="select productkey from product where barcode=%s"
                myvalues=[(row[0])]
                cursor.execute(sqlst, myvalues)
                productkey = cursor.fetchall()
                barcode=row[0]
                productname=row[1]
                purchaseprice=row[2]
                quantity = row[3]
                linetotal=row[4]


                sqlst="""insert into goodsreceiptdetail (goodsreceiptkey, productkey, purchaseprice, quantity, linetotal,
                 productname, barcode, warehousekey) values (%s, %s,%s,%s,%s,%s,%s, %s )"""
                myvalues=[(goodsreceiptkey), (productkey), (purchaseprice), (quantity), (linetotal), (productname), (barcode), (warehousekey) ]
                cursor.execute(sqlst, myvalues)

                # get existing qty
                sqlst="""select onhandquantity from inventory where productkey=%s and warehousekey=%s"""
                values=[(productkey), (warehousekey)]
                cursor.execute(sqlst, values)
                qtydata =cursor.fetchall()
                if (qtydata):
                    updatedquantity=(int(qtydata[0][0]) + int(quantity))
                    # update qty
                    sqlst="""update inventory set onhandquantity=%s where productkey=%s and warehousekey=%s"""
                    values=[ (updatedquantity) , (productkey), (warehousekey)]
                    cursor.execute(sqlst, values)
                else:
                    goodsreceiptkey=0
                    print ('Product does not exist in Inventory table')
                    mysql.connection.rollback()

            mysql.connection.commit()

            return jsonify(goodsreceiptkey)
        else:
            return render_template('accounts/goodsreceipt.html', form=mygoodsreceiptform)
    else:
        return redirect (url_for('login'))








@app.route('/searchproductname', methods=['GET','POST'])
def searchproductname():
    mysaleform=SaleForm(request.form)
    myloginform=LoginForm(request.form)
    if 'usersessionid' in session:
        if request.method=='POST':
            try:
                barcode= request.form['barcode']
                cursor=mysql.connection.cursor()
                sqlst="select productname from product where barcode=%s"
                myval=[(barcode)]
                cursor.execute(sqlst, myval)
                productdetails=cursor.fetchall()
            except Exception as err:
                print (err)
            return jsonify (productdetails)
        else:
            return render_template('accounts/sale2.html', form=mysaleform)
    else:
        return redirect (url_for('login'))




@app.route('/searchproductprice', methods=['GET','POST'])
def searchproductprice():
    if 'usersessionid' in session:
        if request.method=='POST':
            try:
                barcode= request.form['barcode']
                cursor=mysql.connection.cursor()
                sqlst="select saleprice from product where barcode=%s"
                myval=[(barcode)]
                cursor.execute(sqlst, myval)
                productdetails=cursor.fetchall()
            except Exception as err:
                print (err)
            return json.dumps(productdetails, cls=DecimalEncoder)
            # return jsonify(productdetails)
    else:
        return redirect (url_for('login'))




@app.route('/sale', methods=['GET','POST'])
def sale():
    mysaleform=SaleForm(request.form)
    cursor = mysql.connection.cursor()
    sqlst = "select customerkey, customername from customer union all select 0, 'Select Customer' order by customerkey"
    cursor.execute(sqlst)
    allcustomers = cursor.fetchall()
    mysaleform.customername.choices = allcustomers

    if 'usersessionid' in session:
        if request.method=='POST':
            saleordertotal =  request.form['grandtotal']
            customerkey = request.form['customername']
            saledate = request.form['saledate']
            # print (request.form)
            list = [(k, v) for k, v in dict.items(request.form)]
            # print (list)
            productslist = list[0][1]
            chunks = [productslist[x:x+5] for x in range (0,len(productslist),5)]

            usersessionid=session['usersessionid']
            sqlst = """insert into saleorder ( saleordertotal ,  usersessionid, userkey, 
            storekey, poskey, warehousekey, customerkey, saleorderdate) values (%s, %s, %s, %s, %s, %s, %s, %s)"""

            myvalues=[(saleordertotal), (usersessionid), (session['userkey']), (session['storekey']), (session['poskey']), (session['warehousekey']), (customerkey), (saledate)]
            cursor=mysql.connection.cursor()
            cursor.execute(sqlst, myvalues)


            sqlst="select saleorderkey from saleorder where usersessionid=%s and saleorderkey=(select LAST_INSERT_ID())"
            myvalues=[(usersessionid)]
            cursor.execute(sqlst, myvalues)
            saleorderkey=cursor.fetchall()
            # print (saleorderkey)

            for row in chunks:
                # print (row)
                # get productkey
                # print (row[0])
                sqlst="select productkey from product where barcode=%s"
                myvalues=[(row[0])]
                cursor.execute(sqlst, myvalues)
                productkey = cursor.fetchall()
                barcode=row[0]
                productname=row[1]
                saleprice=row[2]
                quantity = row[3]
                linetotal=row[4]


                sqlst="""insert into saleorderdetail (saleorderkey, productkey, saleprice, quantity, linetotal,
                 productname, barcode) values (%s, %s,%s,%s,%s,%s,%s )"""
                myvalues=[(saleorderkey), (productkey), (saleprice), (quantity), (linetotal), (productname), (barcode) ]
                cursor.execute(sqlst, myvalues)

                # get existing inventory
                sqlst="select onhandquantity from inventory where productkey=%s and warehousekey=%s"
                values = [(productkey), (session['warehousekey'])]
                cursor.execute(sqlst, values)
                onhandqty = cursor.fetchall()
                updatedqty = int(onhandqty[0][0]) - int(quantity)

                # update inventory
                sqlst="""update inventory set onhandquantity=%s where productkey=%s and warehousekey=%s"""
                values=[(updatedqty), (productkey), (session['warehousekey'])]
                cursor.execute(sqlst, values)

            mysql.connection.commit()

            return jsonify(saleorderkey)
        else:
            return render_template('accounts/sale2.html', form=mysaleform)
    else:
        return redirect (url_for('login'))




@app.route('/goodsissue', methods=['GET','POST'])
def goodsissue():
    mygoodsissueform=GoodsIssueForm(request.form)
    cursor = mysql.connection.cursor()
    sqlst = "select warehousekey, warehousename from warehouse union all select 0, 'Select Warehouse' order by warehousekey"
    cursor.execute(sqlst)
    allwarehouses = cursor.fetchall()
    mygoodsissueform.warehousename.choices = allwarehouses

    if 'usersessionid' in session:
        if request.method=='POST':
            goodsissuetotal =  request.form['grandtotal']
            warehousename = request.form['warehousename']
            goodsissuedate = request.form['goodsissuedate']
            reason = request.form['reason']

            # print (request.form)
            list = [(k, v) for k, v in dict.items(request.form)]
            # print (list)
            productslist = list[0][1]
            chunks = [productslist[x:x+5] for x in range (0,len(productslist),5)]

            usersessionid=session['usersessionid']
            sqlst = """insert into goodsissue ( goodsissuetotal ,  usersessionid, userkey, 
             warehousekey, reason, goodsissuedate) values (%s, %s, %s, %s, %s, %s)"""

            myvalues=[(goodsissuetotal), (usersessionid), (session['userkey']), (warehousename),  (reason), (goodsissuedate)]
            cursor=mysql.connection.cursor()
            cursor.execute(sqlst, myvalues)


            sqlst="select goodsissuekey from goodsissue where usersessionid=%s and goodsissuekey=(select LAST_INSERT_ID())"
            myvalues=[(usersessionid)]
            cursor.execute(sqlst, myvalues)
            goodsissuekey=cursor.fetchall()
            # print (saleorderkey)

            for row in chunks:
                # print (row)
                # get productkey
                # print (row[0])
                sqlst="select productkey from product where barcode=%s"
                myvalues=[(row[0])]
                cursor.execute(sqlst, myvalues)
                productkey = cursor.fetchall()
                barcode=row[0]
                productname=row[1]
                saleprice=row[2]
                quantity = row[3]
                linetotal=row[4]


                sqlst="""insert into goodsissuedetail (goodsissuekey, productkey, saleprice, quantity, linetotal,
                 productname, barcode) values (%s, %s,%s,%s,%s,%s,%s )"""
                myvalues=[(goodsissuekey), (productkey), (saleprice), (quantity), (linetotal), (productname), (barcode) ]
                cursor.execute(sqlst, myvalues)

                # get existing inventory
                sqlst="select onhandquantity from inventory where productkey=%s and warehousekey=%s"
                values = [(productkey), (warehousename)]
                cursor.execute(sqlst, values)
                onhandqty = cursor.fetchall()
                updatedqty = int(onhandqty[0][0]) - int(quantity)

                # update inventory
                sqlst="""update inventory set onhandquantity=%s where productkey=%s and warehousekey=%s"""
                values=[(updatedqty), (productkey), (warehousename)]
                cursor.execute(sqlst, values)

            mysql.connection.commit()

            return jsonify(goodsissuekey)
        else:
            return render_template('accounts/goodsissue.html', form=mygoodsissueform)
    else:
        return redirect (url_for('login'))








@app.route('/searchrefundorders', methods=['GET','POST'])
def searchrefundorders():
    myrefundordersearchform=RefundOrderSearchForm(request.form)
    cursor = mysql.connection.cursor()
    cursor.execute("select brandkey, brandname from brand union all select 0, 'Select Brand' order by brandkey ")
    allbrands = cursor.fetchall()
    myrefundordersearchform.brandname.choices = allbrands

    cursor.execute("select vendorkey, vendorname from vendor union all select 0, 'Select Vendor' order by vendorkey ")
    allvendors = cursor.fetchall()
    myrefundordersearchform.vendorname.choices = allvendors

    cursor.execute(
        "select categorykey, categoryname from category union all select 0, 'Select Category' order by categorykey ")
    allcategories = cursor.fetchall()
    myrefundordersearchform.categoryname.choices = allcategories

    if 'usersessionid' in session:
        if request.method=='POST':
            try:
                startdate=request.form['startdate']
                enddate = request.form['enddate']
                saleorderkey= request.form['saleorderkey']
                categorykey = request.form['categoryname']
                vendorkey = request.form['vendorname']
                brandkey = request.form['brandname']
                productname = request.form['productname']
                barcode = request.form['barcode']
                saleprice = request.form['saleprice']

                conditions = ' where storekey=%s and poskey=%s and 1=1 '

                if (len(startdate) > 0):
                    conditions = conditions + " and date(refundorderdate) >= date('" + startdate + "')"

                if (len(enddate) > 0):
                    conditions = conditions + " and date(refundorderdate) <= date('" + enddate + "')"

                if (len(saleorderkey) > 0):
                    conditions = conditions + " and saleorderkey = '" + saleorderkey + "'"

                if (int(categorykey) > 0):
                    conditions = conditions + " and product.categorykey = '" + categorykey + "'"

                if (int(vendorkey) > 0):
                    conditions = conditions + " and product.vendorkey = '" + vendorkey + "'"

                if (int(brandkey) > 0):
                    conditions = conditions + " and product.brandkey = '" + brandkey + "'"

                if (len(productname)>0) :
                    conditions = conditions + " and product.productname = '" + productname + "'"

                if (len(barcode)>0) :
                    conditions = conditions + " and product.barcode = '" + barcode + "'"

                    if (len(saleprice) > 0):
                        conditions = conditions + " and refundorderdetail.saleprice = '" + saleprice + "'"




                cursor=mysql.connection.cursor(cursorclass=MySQLdb.cursors.DictCursor)
                sqlst="""select distinct refundorder.refundorderkey, refundorder.refundorderdate, refundorder.refundordertotal, refundorder.saleorderkey
                 from refundorder 
                left join refundorderdetail on refundorder.refundorderkey=refundorderdetail.refundorderkey 
                left join product on refundorderdetail.productkey=product.productkey
                """ + conditions
                values = [(session['storekey']), (session['poskey'])]
                cursor.execute(sqlst, values)
                productdetails=cursor.fetchall()
            except Exception as err:
                print (err)
            return render_template('accounts/refundordersearch.html', form=myrefundordersearchform ,productdetails=productdetails)

        if request.method=='GET':
            try:
                cursor=mysql.connection.cursor(cursorclass=MySQLdb.cursors.DictCursor)
                sqlst="""select refundorder.*, saleorder.saleordertotal from refundorder
                left join saleorder on refundorder.saleorderkey=saleorder.saleorderkey
                where refundorder.storekey=%s and refundorder.poskey=%s
                order by refundorderdate, refundorderkey"""
                values=[(session['storekey']), (session['poskey'])]
                cursor.execute(sqlst, values)
                productdetails=cursor.fetchall()
            except Exception as err:
                print (err)
            return render_template('accounts/refundordersearch.html', form=myrefundordersearchform ,productdetails=productdetails)
    else:
        return redirect (url_for('login'))








@app.route('/searchproductalldata',  methods=['GET','POST'])
def searchproductalldata():
    if 'usersessionid' in session:
        myproductsearchform=ProductSearchForm(request.form)
        cursor = mysql.connection.cursor()
        cursor.execute("select brandkey, brandname from brand union all select 0, 'Select Brand' order by brandkey ")
        allbrands = cursor.fetchall()
        myproductsearchform.brandname.choices = allbrands

        cursor.execute("select vendorkey, vendorname from vendor union all select 0, 'Select Vendor' order by vendorkey ")
        allvendors = cursor.fetchall()
        myproductsearchform.vendorname.choices = allvendors

        cursor.execute(
            "select categorykey, categoryname from category union all select 0, 'Select Category' order by categorykey ")
        allcategories = cursor.fetchall()
        myproductsearchform.categoryname.choices = allcategories


        if request.method=='POST':
            try:
                categorykey= request.form['categoryname']
                vendorkey = request.form['vendorname']
                brandkey = request.form['brandname']
                barcode = request.form['barcode']
                productname = request.form['productname']
                productid = request.form['productid']

                conditions = ' where 1=1 '

                if (int(categorykey) > 0):
                    conditions = conditions + " and product.categorykey = '" + categorykey + "'"

                if (int(vendorkey) > 0):
                    conditions = conditions + " and product.vendorkey = '" + vendorkey + "'"

                if (int(brandkey) > 0):
                    conditions = conditions + " and product.brandkey = '" + brandkey + "'"

                if (len(productname)>0) :
                    conditions = conditions + " and product.productname = '" + productname + "'"

                if (len(productid)>0) :
                    conditions = conditions + " and product.productid = '" + productid + "'"

                if (len(barcode)>0) :
                    conditions = conditions + " and product.barcode = '" + barcode + "'"


                print (conditions)

                cursor=mysql.connection.cursor(cursorclass=MySQLdb.cursors.DictCursor)
                sqlst="""select productid , productkey , barcode, productname,  categoryname, saleprice , brandname, vendorname from product 
                left join category on product.categorykey=category.categorykey
                left join brand on product.brandkey=brand.brandkey
                left join vendor on product.vendorkey=vendor.vendorkey
                """ + conditions

                # print (sqlst)

                cursor.execute(sqlst)

                productdetails=cursor.fetchall()
            except Exception as err:
                print (err)
            return render_template('accounts/productsearch.html', form=myproductsearchform ,productdetails=productdetails)

        if request.method=='GET':
            try:
                cursor=mysql.connection.cursor(cursorclass=MySQLdb.cursors.DictCursor)
                sqlst="""select productid , productkey , barcode, productname,  categoryname, saleprice , brandname, vendorname from product 
                left join category on product.categorykey=category.categorykey
                left join brand on product.brandkey=brand.brandkey
                left join vendor on product.vendorkey=vendor.vendorkey
                order by barcode """

                cursor.execute(sqlst)
                productdetails=cursor.fetchall()
            except Exception as err:
                print (err)
            return render_template('accounts/productsearch.html', form=myproductsearchform ,productdetails=productdetails)
    else:
        return redirect (url_for('login'))






@app.route('/searchstore',  methods=['GET','POST'])
def searchstore():
    if 'usersessionid' in session:
        mystoresearchform=StoreSearchForm(request.form)
        cursor = mysql.connection.cursor()
        cursor.execute("select warehousekey, warehousename from warehouse union all select 0, 'Select Warehouse' order by warehousekey ")
        allwarehouses = cursor.fetchall()
        mystoresearchform.warehousename.choices = allwarehouses

        cursor.execute("select customerkey, customername from customer union all select 0, 'Select Customer' order by customerkey ")
        allcustomers = cursor.fetchall()
        mystoresearchform.defaultcustomername.choices = allcustomers

        if request.method=='POST':
            try:
                warehousekey= request.form['warehousename']
                customerkey = request.form['defaultcustomername']
                storename = request.form['storename']
                storeid = request.form['storeid']

                conditions = ' where 1=1 '

                if (int(warehousekey) > 0):
                    conditions = conditions + " and store.warehousekey = '" + warehousekey + "'"

                if (int(customerkey) > 0):
                    conditions = conditions + " and store.defaultcustomerkey = '" + customerkey + "'"

                if (len(storename) > 0):
                    conditions = conditions + " and store.storename = '" + storename + "'"

                if (len(storeid)>0) :
                    conditions = conditions + " and store.storeid = '" + storeid + "'"


                print (conditions)

                cursor=mysql.connection.cursor(cursorclass=MySQLdb.cursors.DictCursor)
                sqlst="""select storekey , storeid, storename,  warehousename, customername from store 
                left join warehouse on store.warehousekey=warehouse.warehousekey
                left join customer on store.defaultcustomerkey=customer.customerkey
                """ + conditions

                # print (sqlst)

                cursor.execute(sqlst)

                productdetails=cursor.fetchall()
            except Exception as err:
                print (err)
            return render_template('accounts/storesearch.html', form=mystoresearchform ,productdetails=productdetails)

        if request.method=='GET':
            try:
                cursor=mysql.connection.cursor(cursorclass=MySQLdb.cursors.DictCursor)
                sqlst="""select storekey , storeid, storename,  warehousename, customername from store 
                left join warehouse on store.warehousekey=warehouse.warehousekey
                left join customer on store.defaultcustomerkey=customer.customerkey
                order by storename """

                cursor.execute(sqlst)
                productdetails=cursor.fetchall()
            except Exception as err:
                print (err)
            return render_template('accounts/storesearch.html', form=mystoresearchform ,productdetails=productdetails)
    else:
        return redirect (url_for('login'))






@app.route('/searchpos',  methods=['GET','POST'])
def searchpos():
    if 'usersessionid' in session:
        mypossearchform=POSSearchForm(request.form)
        cursor = mysql.connection.cursor()
        cursor.execute("select storekey, storename from store union all select 0, 'Select Store' order by storekey ")
        allwarehouses = cursor.fetchall()
        mypossearchform.storename.choices = allwarehouses



        if request.method=='POST':
            try:
                posname= request.form['posname']
                storekey = request.form['storename']
                posid = request.form['posid']

                conditions = ' where 1=1 '

                if (int(storekey) > 0):
                    conditions = conditions + " and pos.storekey = '" + storekey + "'"

                if (len(posname) > 0):
                    conditions = conditions + " and pos.posname = '" + posname + "'"

                if (len(posid)>0) :
                    conditions = conditions + " and pos.posid = '" + posid + "'"


                print (conditions)

                cursor=mysql.connection.cursor(cursorclass=MySQLdb.cursors.DictCursor)
                sqlst="""select poskey , posid, storename,  posname  from pos 
                left join store on pos.storekey=store.storekey
                """ + conditions

                # print (sqlst)

                cursor.execute(sqlst)

                productdetails=cursor.fetchall()
            except Exception as err:
                print (err)
            return render_template('accounts/possearch.html', form=mypossearchform ,productdetails=productdetails)

        if request.method=='GET':
            try:
                cursor=mysql.connection.cursor(cursorclass=MySQLdb.cursors.DictCursor)
                sqlst="""select poskey , posid, storename,  posname  from pos 
                left join store on pos.storekey=store.storekey
                order by poskey """

                cursor.execute(sqlst)
                productdetails=cursor.fetchall()
            except Exception as err:
                print (err)
            return render_template('accounts/possearch.html', form=mypossearchform ,productdetails=productdetails)
    else:
        return redirect (url_for('login'))






@app.route('/searchcustomer',  methods=['GET','POST'])
def searchcustomer():
    if 'usersessionid' in session:
        mycustomersearchform=CustomerSearchForm(request.form)
        if request.method=='POST':
            try:
                customerid= request.form['customerid']
                customername = request.form['customername']

                conditions = ' where 1=1 '

                if (len(customerid) > 0):
                    conditions = conditions + " and customer.customerid = '" + customerid + "'"

                if (len(customername) > 0):
                    conditions = conditions + " and customer.customername = '" + customername + "'"



                cursor=mysql.connection.cursor(cursorclass=MySQLdb.cursors.DictCursor)
                sqlst="""select * from customer  """ + conditions

                # print (sqlst)

                cursor.execute(sqlst)

                productdetails=cursor.fetchall()
            except Exception as err:
                print (err)
            return render_template('accounts/customersearch.html', form=mycustomersearchform ,productdetails=productdetails)

        if request.method=='GET':
            try:
                cursor=mysql.connection.cursor(cursorclass=MySQLdb.cursors.DictCursor)
                sqlst="""select * from customer 
                 order by customer.customerkey
                 """

                cursor.execute(sqlst)
                productdetails=cursor.fetchall()
            except Exception as err:
                print (err)
            return render_template('accounts/customersearch.html', form=mycustomersearchform ,productdetails=productdetails)
    else:
        return redirect (url_for('login'))




@app.route('/searchcategory',  methods=['GET','POST'])
def searchcategory():
    if 'usersessionid' in session:
        mycategorysearchform=CategorySearchForm(request.form)
        if request.method=='POST':
            try:
                categoryid= request.form['categoryid']
                categoryname = request.form['categoryname']

                conditions = ' where 1=1 '

                if (len(categoryid) > 0):
                    conditions = conditions + " and category.categoryid = '" + categoryid + "'"

                if (len(categoryname) > 0):
                    conditions = conditions + " and category.categoryname = '" + categoryname + "'"

                cursor=mysql.connection.cursor(cursorclass=MySQLdb.cursors.DictCursor)
                sqlst="""select * from category  """ + conditions

                # print (sqlst)

                cursor.execute(sqlst)

                productdetails=cursor.fetchall()
            except Exception as err:
                print (err)
            return render_template('accounts/categorysearch.html', form=mycategorysearchform ,productdetails=productdetails)

        if request.method=='GET':
            try:
                cursor=mysql.connection.cursor(cursorclass=MySQLdb.cursors.DictCursor)
                sqlst="""select * from category 
                 order by category.categorykey
                 """

                cursor.execute(sqlst)
                productdetails=cursor.fetchall()
            except Exception as err:
                print (err)
            return render_template('accounts/categorysearch.html', form=mycategorysearchform ,productdetails=productdetails)
    else:
        return redirect (url_for('login'))




@app.route('/searchwarehouse',  methods=['GET','POST'])
def searchwarehouse():
    if 'usersessionid' in session:
        mywarehousesearchform=WarehouseSearchForm(request.form)
        if request.method=='POST':
            try:
                warehouseid= request.form['warehouseid']
                warehousename = request.form['warehousename']

                conditions = ' where 1=1 '

                if (len(warehouseid) > 0):
                    conditions = conditions + " and warehouse.warehouseid = '" + warehouseid + "'"

                if (len(warehousename) > 0):
                    conditions = conditions + " and warehouse.warehousename = '" + warehousename + "'"



                cursor=mysql.connection.cursor(cursorclass=MySQLdb.cursors.DictCursor)
                sqlst="""select * from warehouse  """ + conditions

                # print (sqlst)

                cursor.execute(sqlst)

                productdetails=cursor.fetchall()
            except Exception as err:
                print (err)
            return render_template('accounts/warehousesearch.html', form=mywarehousesearchform ,productdetails=productdetails)

        if request.method=='GET':
            try:
                cursor=mysql.connection.cursor(cursorclass=MySQLdb.cursors.DictCursor)
                sqlst="""select * from warehouse 
                 order by warehouse.warehousekey
                 """

                cursor.execute(sqlst)
                productdetails=cursor.fetchall()
            except Exception as err:
                print (err)
            return render_template('accounts/warehousesearch.html', form=mywarehousesearchform ,productdetails=productdetails)
    else:
        return redirect (url_for('login'))






@app.route('/searchvendor',  methods=['GET','POST'])
def searchvendor():
    if 'usersessionid' in session:
        myvendorsearchform=VendorSearchForm(request.form)
        if request.method=='POST':
            try:
                vendorid= request.form['vendorid']
                vendorname = request.form['vendorname']

                conditions = ' where 1=1 '

                if (len(vendorid) > 0):
                    conditions = conditions + " and vendor.vendorid = '" + vendorid + "'"

                if (len(vendorname) > 0):
                    conditions = conditions + " and vendor.vendorname = '" + vendorname + "'"



                cursor=mysql.connection.cursor(cursorclass=MySQLdb.cursors.DictCursor)
                sqlst="""select * from vendor  """ + conditions

                # print (sqlst)

                cursor.execute(sqlst)

                productdetails=cursor.fetchall()
            except Exception as err:
                print (err)
            return render_template('accounts/vendorsearch.html', form=myvendorsearchform ,productdetails=productdetails)

        if request.method=='GET':
            try:
                cursor=mysql.connection.cursor(cursorclass=MySQLdb.cursors.DictCursor)
                sqlst="""select * from vendor 
                 order by vendor.vendorkey
                 """

                cursor.execute(sqlst)
                productdetails=cursor.fetchall()
            except Exception as err:
                print (err)
            return render_template('accounts/vendorsearch.html', form=myvendorsearchform ,productdetails=productdetails)
    else:
        return redirect (url_for('login'))




@app.route('/searchbrand',  methods=['GET','POST'])
def searchbrand():
    if 'usersessionid' in session:
        mybrandsearchform=BrandSearchForm(request.form)
        if request.method=='POST':
            try:
                brandid= request.form['brandid']
                brandname = request.form['brandname']

                conditions = ' where 1=1 '

                if (len(brandid) > 0):
                    conditions = conditions + " and brand.brandid = '" + brandid + "'"

                if (len(brandname) > 0):
                    conditions = conditions + " and brand.brandname = '" + brandname + "'"



                cursor=mysql.connection.cursor(cursorclass=MySQLdb.cursors.DictCursor)
                sqlst="""select * from brand  """ + conditions

                # print (sqlst)

                cursor.execute(sqlst)

                productdetails=cursor.fetchall()
            except Exception as err:
                print (err)
            return render_template('accounts/brandsearch.html', form=mybrandsearchform ,productdetails=productdetails)

        if request.method=='GET':
            try:
                cursor=mysql.connection.cursor(cursorclass=MySQLdb.cursors.DictCursor)
                sqlst="""select * from brand 
                 order by brand.brandkey
                 """

                cursor.execute(sqlst)
                productdetails=cursor.fetchall()
            except Exception as err:
                print (err)
            return render_template('accounts/brandsearch.html', form=mybrandsearchform ,productdetails=productdetails)
    else:
        return redirect (url_for('login'))







@app.route('/searchinventory',  methods=['GET','POST'])
def searchinventory():
    if 'usersessionid' in session:
        myinventorysearchform=InventorySearchForm(request.form)
        cursor = mysql.connection.cursor()
        cursor.execute("select brandkey, brandname from brand union all select 0, 'Select Brand' order by brandkey ")
        allbrands = cursor.fetchall()
        myinventorysearchform.brandname.choices = allbrands

        cursor.execute("select vendorkey, vendorname from vendor union all select 0, 'Select Vendor' order by vendorkey ")
        allvendors = cursor.fetchall()
        myinventorysearchform.vendorname.choices = allvendors

        cursor.execute(
            "select categorykey, categoryname from category union all select 0, 'Select Category' order by categorykey ")
        allcategories = cursor.fetchall()
        myinventorysearchform.categoryname.choices = allcategories

        cursor.execute(
            "select warehousekey, warehousename from warehouse union all select 0, 'Select Warehouse' order by warehousekey ")
        allwarehouses = cursor.fetchall()
        myinventorysearchform.warehousename.choices = allwarehouses


        if request.method=='POST':
            try:
                categorykey= request.form['categoryname']
                vendorkey = request.form['vendorname']
                brandkey = request.form['brandname']
                warehousekey = request.form['warehousename']
                barcode = request.form['barcode']
                productname = request.form['productname']
                saleprice = request.form['saleprice']

                conditions = ' where 1=1 '

                if (int(categorykey) > 0):
                    conditions = conditions + " and product.categorykey = '" + categorykey + "'"

                if (int(vendorkey) > 0):
                    conditions = conditions + " and product.vendorkey = '" + vendorkey + "'"

                if (int(brandkey) > 0):
                    conditions = conditions + " and product.brandkey = '" + brandkey + "'"

                if (int(warehousekey) > 0):
                    conditions = conditions + " and inventory.warehousekey = '" + warehousekey + "'"

                if (len(productname)>0) :
                    conditions = conditions + " and product.productname = '" + productname + "'"

                if (len(barcode)>0) :
                    conditions = conditions + " and product.barcode = '" + barcode + "'"

                if (len(saleprice)>0) :
                    conditions = conditions + " and product.saleprice = '" + saleprice + "'"


                print (conditions)

                cursor=mysql.connection.cursor(cursorclass=MySQLdb.cursors.DictCursor)
                sqlst="""select product.productkey , barcode, productname,  categoryname, saleprice , brandname, 
                vendorname , warehousename, onhandquantity
                from product 
                left join inventory on product.productkey =  inventory.productkey
                left join warehouse on inventory.warehousekey=warehouse.warehousekey
                left join category on product.categorykey=category.categorykey
                left join brand on product.brandkey=brand.brandkey
                left join vendor on product.vendorkey=vendor.vendorkey
                """ + conditions

                # print (sqlst)

                cursor.execute(sqlst)

                productdetails=cursor.fetchall()
            except Exception as err:
                print (err)
            return render_template('accounts/inventorysearch.html', form=myinventorysearchform ,productdetails=productdetails)

        if request.method=='GET':
            try:
                cursor=mysql.connection.cursor(cursorclass=MySQLdb.cursors.DictCursor)
                sqlst="""select product.productkey , barcode, productname,  categoryname, saleprice , brandname, vendorname
                 , warehousename, onhandquantity from product 
                left join inventory on product.productkey=inventory.productkey
                left join warehouse on  inventory.warehousekey=warehouse.warehousekey
                left join category on product.categorykey=category.categorykey
                left join brand on product.brandkey=brand.brandkey
                left join vendor on product.vendorkey=vendor.vendorkey
                order by barcode """

                cursor.execute(sqlst)
                productdetails=cursor.fetchall()
            except Exception as err:
                print (err)
            return render_template('accounts/inventorysearch.html', form=myinventorysearchform ,productdetails=productdetails)
    else:
        return redirect (url_for('login'))










@app.route('/savegrpo', methods=['GET','POST'])
def savegrpo():
    mygrpoform=GRPOForm(request.form)
    if 'usersessionid' in session:
        if request.method=='POST':
            grpototal =  request.form['grandtotal']
            vendorkey=request.form['vendorkey']
            orderdate= request.form['orderdate']
            receiptdate = request.form['receiptdate']
            warehousekey=request.form['warehousekey']
            status=request.form['warehousekey']
            # print (request.form)
            list = [(k, v) for k, v in dict.items(request.form)]
            # print (list)
            productslist = list[0][1]
            chunks = [productslist[x:x+5] for x in range (0,len(productslist),5)]

            usersessionid=session['usersessionid']
            sqlst = """insert into grpo ( grpototal ,  usersessionid, userkey, 
            vendorkey, orderdate, receiptdate, warehousekey, status) values (%s, %s, %s, %s, %s, %s, %s, %s)"""

            myvalues=[(grpototal), (usersessionid), (session['userkey']), (vendorkey), (orderdate), (receiptdate), (warehousekey), (status)]
            cursor=mysql.connection.cursor()
            cursor.execute(sqlst, myvalues)


            sqlst="select grpokey from grpo where usersessionid=%s and grpokey=(select LAST_INSERT_ID())"
            myvalues=[(usersessionid)]
            cursor.execute(sqlst, myvalues)
            grpokey=cursor.fetchall()
            # print (saleorderkey)

            for row in chunks:
                # print (row)
                # get productkey
                # print (row[0])
                sqlst="select productkey from product where barcode=%s"
                myvalues=[(row[0])]
                cursor.execute(sqlst, myvalues)
                productkey = cursor.fetchall()
                barcode=row[0]
                productname=row[1]
                purchaseprice=row[2]
                quantity = row[3]
                linetotal=row[4]


                sqlst="""insert into grpodetail (grpokey, productkey, purchaseprice, quantity, linetotal,
                 productname, barcode, warehousekey) values (%s, %s,%s,%s,%s,%s,%s )"""
                myvalues=[(grpokey), (productkey), (purchaseprice), (quantity), (linetotal), (productname), (barcode), (warehousekey) ]
                cursor.execute(sqlst, myvalues)

            mysql.connection.commit()

            return jsonify(grpokey)
        else:
            return render_template('accounts/sale2.html', form=mygrpoform)
    else:
        return redirect (url_for('login'))











@app.route('/getsaleorderdetails', methods=['GET', 'POST'])
def getsaleorderdetails():
    if 'usersessionid' in session:
        if request.method=='POST':
            saleorderkey=request.form['saleorderkey']
            cursor = mysql.connection.cursor(cursorclass=MySQLdb.cursors.DictCursor)
            sqlst = """ select saleorder.saleorderkey, saleorderdetail.saleorderdetailkey  , saleorderdetail.productkey, 
                        product.barcode ,  saleorderdetail.productname, quantity, 
                        saleorderdetail.saleprice, linetotal from saleorder
                        left join saleorderdetail on saleorder.saleorderkey=saleorderdetail.saleorderkey 
                        left join product on saleorderdetail.productkey=product.productkey 
                        where saleorder.saleorderkey=%s and storekey=%s and poskey=%s"""
            values = [(saleorderkey), (session['storekey']), (session['poskey'])]
            cursor.execute(sqlst, values)
            saleorderdetails = cursor.fetchall()
            return json.dumps(saleorderdetails, cls=DecimalEncoder)
    else:
        return redirect (url_for('login'))




@app.route('/getgoodsissuedetails', methods=['GET', 'POST'])
def getgoodsissuedetails():
    if 'usersessionid' in session:
        if request.method=='POST':
            goodsissuekey=request.form['goodsissuekey']
            cursor = mysql.connection.cursor(cursorclass=MySQLdb.cursors.DictCursor)
            sqlst = """ select goodsissue.goodsissuekey, goodsissuedetail.goodsissuedetailkey  , goodsissuedetail.productkey, 
                        product.barcode ,  goodsissuedetail.productname, quantity, 
                        goodsissuedetail.saleprice, linetotal from goodsissue
                        left join goodsissuedetail on goodsissue.goodsissuekey=goodsissuedetail.goodsissuekey 
                        left join product on goodsissuedetail.productkey=product.productkey 
                        where goodsissue.goodsissuekey=%s """
            values = [(goodsissuekey)]
            cursor.execute(sqlst, values)
            saleorderdetails = cursor.fetchall()
            return json.dumps(saleorderdetails, cls=DecimalEncoder)
    else:
        return redirect (url_for('login'))






@app.route('/getgrpodetails', methods=['GET', 'POST'])
def getgrpodetails():
    if 'usersessionid' in session:
        if request.method=='POST':
            grpokey=request.form['grpokey']
            cursor = mysql.connection.cursor(cursorclass=MySQLdb.cursors.DictCursor)
            sqlst = """ select grpo.grpokey, grpodetail.grpodetailkey  , grpodetail.productkey, 
                        product.barcode ,  grpodetail.productname, quantity, 
                        grpodetail.purchaseprice, linetotal from grpo
                        left join grpodetail on grpo.grpokey=grpodetail.grpokey 
                        left join product on grpodetail.productkey=product.productkey 
                        where grpo.grpokey=%s and grpo.warehousekey=%s """
            values = [(grpokey), (session['warehousekey'])]
            cursor.execute(sqlst, values)
            saleorderdetails = cursor.fetchall()
            return json.dumps(saleorderdetails, cls=DecimalEncoder)
    else:
        return redirect (url_for('login'))





@app.route('/getgoodsreceiptdetails', methods=['GET', 'POST'])
def getgoodsreceiptdetails():
    if 'usersessionid' in session:
        if request.method=='POST':
            goodsreceiptkey=request.form['goodsreceiptkey']
            cursor = mysql.connection.cursor(cursorclass=MySQLdb.cursors.DictCursor)
            sqlst = """ select goodsreceipt.goodsreceiptkey, goodsreceiptdetail.goodsreceiptdetailkey  , goodsreceiptdetail.productkey, 
                        product.barcode ,  goodsreceiptdetail.productname, quantity, 
                        goodsreceiptdetail.purchaseprice, linetotal from goodsreceipt
                        left join goodsreceiptdetail on goodsreceipt.goodsreceiptkey=goodsreceiptdetail.goodsreceiptkey 
                        left join product on goodsreceiptdetail.productkey=product.productkey 
                        where goodsreceipt.goodsreceiptkey=%s """
            values = [(goodsreceiptkey)]
            cursor.execute(sqlst, values)
            saleorderdetails = cursor.fetchall()
            return json.dumps(saleorderdetails, cls=DecimalEncoder)
    else:
        return redirect (url_for('login'))









@app.route('/getsaleorder', methods=['GET', 'POST'])
def getsaleorder():
    if 'usersessionid' in session:
        if request.method=='POST':
            saleorderkey=request.form['saleorderkey']
            cursor = mysql.connection.cursor(cursorclass=MySQLdb.cursors.DictCursor)
            sqlst = """ select * from saleorder
                        where storekey=%s and poskey=%s and saleorder.saleorderkey=%s"""
            values = [(session['storekey']), (session['poskey']), (saleorderkey) ]
            cursor.execute(sqlst, values)
            saleorderdetails = cursor.fetchall()
            # print (saleorderdetails)
            return jsonify(saleorderdetails)
    else:
        return redirect (url_for('login'))




@app.route('/getsaleordertotal', methods=['GET', 'POST'])
def getsaleordertotal():
    if 'usersessionid' in session:
        if request.method=='POST':
            saleorderkey=request.form['saleorderkey']
            cursor = mysql.connection.cursor(cursorclass=MySQLdb.cursors.DictCursor)
            sqlst = """ select saleordertotal from saleorder
                        where storekey=%s and poskey=%s and saleorder.saleorderkey=%s"""
            values = [(session['storekey']), (session['poskey']), (saleorderkey) ]
            cursor.execute(sqlst, values)
            saleorderdetails = cursor.fetchall()
            # print (saleorderdetails)
            return json.dumps(saleorderdetails, cls=DecimalEncoder)
    else:
        return redirect (url_for('login'))





@app.route('/getproduct', methods=['GET', 'POST'])
def getproduct():
    if 'usersessionid' in session:
        if request.method=='POST':
            productkey=request.form['productkey']
            cursor = mysql.connection.cursor(cursorclass=MySQLdb.cursors.DictCursor)
            sqlst = """ select * from product
                        where productkey=%s"""
            values = [(productkey) ]
            cursor.execute(sqlst, values)
            productdetails = cursor.fetchall()
            # print (saleorderdetails)
            return json.dumps(productdetails, cls=DecimalEncoder)
    else:
        return redirect (url_for('login'))




@app.route('/getstore', methods=['GET', 'POST'])
def getstore():
    if 'usersessionid' in session:
        if request.method=='POST':
            storekey=request.form['storekey']
            cursor = mysql.connection.cursor(cursorclass=MySQLdb.cursors.DictCursor)
            sqlst = """ select * from store
                        where storekey=%s"""
            values = [(storekey) ]
            cursor.execute(sqlst, values)
            productdetails = cursor.fetchall()
            # print (saleorderdetails)
            return jsonify(productdetails)
    else:
        return redirect (url_for('login'))






@app.route('/getcustomer', methods=['GET', 'POST'])
def getcustomer():
    if 'usersessionid' in session:
        if request.method=='POST':
            customerkey=request.form['customerkey']
            cursor = mysql.connection.cursor(cursorclass=MySQLdb.cursors.DictCursor)
            sqlst = """ select * from customer
                        where customerkey=%s"""
            values = [(customerkey) ]
            cursor.execute(sqlst, values)
            productdetails = cursor.fetchall()
            # print (saleorderdetails)
            return jsonify(productdetails)
    else:
        return redirect (url_for('login'))





@app.route('/getpos', methods=['GET', 'POST'])
def getpos():
    if 'usersessionid' in session:
        if request.method=='POST':
            poskey=request.form['poskey']
            cursor = mysql.connection.cursor(cursorclass=MySQLdb.cursors.DictCursor)
            sqlst = """ select * from pos
                        where poskey=%s"""
            values = [(poskey) ]
            cursor.execute(sqlst, values)
            productdetails = cursor.fetchall()
            # print (saleorderdetails)
            return jsonify(productdetails)
    else:
        return redirect (url_for('login'))





@app.route('/getcategory', methods=['GET', 'POST'])
def getcategory():
    if 'usersessionid' in session:
        if request.method=='POST':
            categorykey=request.form['categorykey']
            cursor = mysql.connection.cursor(cursorclass=MySQLdb.cursors.DictCursor)
            sqlst = """ select * from category
                        where categorykey=%s"""
            values = [(categorykey) ]
            cursor.execute(sqlst, values)
            productdetails = cursor.fetchall()
            # print (saleorderdetails)
            return jsonify(productdetails)
    else:
        return redirect (url_for('login'))






@app.route('/getwarehouse', methods=['GET', 'POST'])
def getwarehouse():
    if 'usersessionid' in session:
        if request.method=='POST':
            warehousekey=request.form['warehousekey']
            cursor = mysql.connection.cursor(cursorclass=MySQLdb.cursors.DictCursor)
            sqlst = """ select * from warehouse
                        where warehousekey=%s"""
            values = [(warehousekey) ]
            cursor.execute(sqlst, values)
            productdetails = cursor.fetchall()
            # print (saleorderdetails)
            return jsonify(productdetails)
    else:
        return redirect (url_for('login'))




@app.route('/getvendor', methods=['GET', 'POST'])
def getvendor():
    if 'usersessionid' in session:
        if request.method=='POST':
            vendorkey=request.form['vendorkey']
            cursor = mysql.connection.cursor(cursorclass=MySQLdb.cursors.DictCursor)
            sqlst = """ select * from vendor
                        where vendorkey=%s"""
            values = [(vendorkey) ]
            cursor.execute(sqlst, values)
            productdetails = cursor.fetchall()
            # print (saleorderdetails)
            return jsonify(productdetails)
    else:
        return redirect (url_for('login'))




@app.route('/getbrand', methods=['GET', 'POST'])
def getbrand():
    if 'usersessionid' in session:
        if request.method=='POST':
            brandkey=request.form['brandkey']
            cursor = mysql.connection.cursor(cursorclass=MySQLdb.cursors.DictCursor)
            sqlst = """ select * from brand
                        where brandkey=%s"""
            values = [(brandkey) ]
            cursor.execute(sqlst, values)
            productdetails = cursor.fetchall()
            # print (saleorderdetails)
            return jsonify(productdetails)
    else:
        return redirect (url_for('login'))




@app.route('/getcategories', methods=['GET', 'POST'])
def getcategories():
    if 'usersessionid' in session:
        if request.method=='GET':
            cursor = mysql.connection.cursor()
            sqlst = """ select categorykey, categoryname from category"""
            cursor.execute(sqlst)
            categorieslist = cursor.fetchall()
            # print (saleorderdetails)
            return jsonify(categorieslist)
    else:
        return redirect (url_for('login'))




@app.route('/getdefaultcustomer', methods=['GET', 'POST'])
def getdefaultcustomer():
    if 'usersessionid' in session:
        if request.method=='GET':
            cursor = mysql.connection.cursor()
            sqlst = """ select defaultcustomerkey, customername from store 
            left join customer on store.defaultcustomerkey=customer.customerkey where storekey=%s"""
            values=[(session['storekey'])]
            cursor.execute(sqlst, values)
            defaultcustomername = cursor.fetchall()
            # print (saleorderdetails)
            return jsonify(defaultcustomername)
    else:
        return redirect (url_for('login'))







@app.route('/getstores', methods=['GET', 'POST'])
def getstores():
    if 'usersessionid' in session:
        if request.method=='GET':
            cursor = mysql.connection.cursor()
            sqlst = """ select storekey, storename from store"""
            cursor.execute(sqlst)
            storeslist = cursor.fetchall()
            # print (saleorderdetails)
            return jsonify(storeslist)
    else:
        return redirect (url_for('login'))




@app.route('/getwarehouses', methods=['GET', 'POST'])
def getwarehouses():
    if 'usersessionid' in session:
        if request.method=='GET':
            cursor = mysql.connection.cursor()
            sqlst = """ select warehousekey, warehousename from warehouse"""
            cursor.execute(sqlst)
            warehouseslist = cursor.fetchall()
            # print (saleorderdetails)
            return jsonify(warehouseslist)
    else:
        return redirect (url_for('login'))





@app.route('/getcustomers', methods=['GET', 'POST'])
def getcustomers():
    if 'usersessionid' in session:
        if request.method=='GET':
            cursor = mysql.connection.cursor()
            sqlst = """ select customerkey, customername from customer"""
            cursor.execute(sqlst)
            customerslist = cursor.fetchall()
            # print (saleorderdetails)
            return jsonify(customerslist)
    else:
        return redirect (url_for('login'))






@app.route('/getbrands', methods=['GET', 'POST'])
def getbrands():
    if 'usersessionid' in session:
        if request.method=='GET':
            cursor = mysql.connection.cursor()
            sqlst = """ select brandkey, brandname from brand"""
            cursor.execute(sqlst)
            brandslist = cursor.fetchall()
            # print (saleorderdetails)
            return jsonify(brandslist)
    else:
        return redirect (url_for('login'))




@app.route('/getvendors', methods=['GET', 'POST'])
def getvendors():
    if 'usersessionid' in session:
        if request.method=='GET':
            cursor = mysql.connection.cursor()
            sqlst = """ select vendorkey, vendorname from vendor"""
            cursor.execute(sqlst)
            vendorslist = cursor.fetchall()
            # print (saleorderdetails)
            return jsonify(vendorslist)
    else:
        return redirect (url_for('login'))



@app.route('/refund', methods=['GET','POST'])
def refund():
    myrefundform=RefundForm(request.form)
    if 'usersessionid' in session:
        if request.method=='POST':
            usersessionid = session['usersessionid']
            refundordertotal = request.form['refundordertotal']
            saleorderkey = int(request.form['saleorderkey'])
            # print (request.form)
            list = [(k, v) for k, v in dict.items(request.form)]
            productslist = list[0][1]
            # print (productslist)
            chunks = [productslist[x:x+5] for x in range (0,len(productslist),5)]
            # print (chunks)

            cursor = mysql.connection.cursor()

            sqlst="select customerkey from saleorder where saleorderkey=%s"
            values=[(saleorderkey)]
            cursor.execute(sqlst, values)
            customerkey = cursor.fetchall()

            sqlst = """insert into refundorder ( saleorderkey,  usersessionid, refundordertotal, 
            userkey, storekey, poskey, warehousekey, customerkey
            ) values (%s, %s, %s, %s, %s, %s, %s, %s)"""
            values = [ (saleorderkey), (usersessionid), (refundordertotal), (session['userkey']), (session['storekey']),(session['poskey']),(session['warehousekey']), (customerkey)]
            cursor.execute(sqlst, values)

            sqlst = "select refundorderkey from refundorder where usersessionid=%s and refundorderkey=(select LAST_INSERT_ID())"
            values = [(usersessionid)]
            cursor.execute(sqlst, values)
            refundorderkey = cursor.fetchall()

            for row in chunks:
                # print (row)
                # get productkey
                # print (row[0])
                sqlst="select productkey from product where barcode=%s"
                myvalues=[(row[0])]
                cursor.execute(sqlst, myvalues)
                productkey = cursor.fetchall()
                barcode=row[0]
                productname=row[1]
                saleprice=row[2]
                quantity = row[3]
                linetotal=row[4]


                sqlst = """insert into refundorderdetail (refundorderkey, productkey , quantity, saleprice, linetotal , 
                productname, barcode, warehousekey) VALUES (%s, %s,%s,%s,%s,%s, %s, %s)"""
                myval = [(refundorderkey), (productkey), (quantity), (saleprice), (linetotal), (productname), (barcode), (session['warehousekey'])]
                # print(myval)
                cursor.execute(sqlst, myval)



                # get current inventory
                sqlst="""select onhandquantity from inventory where productkey=%s and warehousekey=%s"""
                values = [(productkey),(session['warehousekey'])]
                cursor.execute(sqlst, values)
                existinginventory=cursor.fetchall()
                updatedinventory = (int(existinginventory[0][0]) + int(quantity))


                # update inventory with more stock
                sqlst="""update inventory set onhandquantity =%s where productkey=%s and warehousekey=%s"""
                values = [ (updatedinventory) , (productkey), (session['warehousekey'])]
                cursor.execute(sqlst, values)


            mysql.connection.commit()

            return jsonify(refundorderkey)
        else:
            return render_template('accounts/refund2.html', form=myrefundform)
    else:
        return redirect (url_for('login'))



@app.route('/totalrefundstatus', methods=['GET','POST'])
def totalrefundstatus():
    if request.method=='POST':
        saleorderkey=request.form['saleorderkey']
        cursor = mysql.connection.cursor()
        sqlst=""" select  SUM(saleorderdetail.quantity) totalsoldquantity
        from saleorder 
        left join saleorderdetail on saleorder.saleorderkey=saleorderdetail.saleorderkey
        where saleorder.saleorderkey=%s"""
        values = [(saleorderkey)]
        cursor.execute(sqlst, values)
        soldquantity = cursor.fetchall()
        # print(soldquantity)
        if soldquantity[0] is None:
            totalsoldquantity=0
        else:
            totalsoldquantity=int (soldquantity[0][0])

        sqlst = """ select SUM(refundorderdetail.quantity) as totalrefundedquantity
        from refundorder
            left join refundorderdetail on  refundorder.refundorderkey=refundorderdetail.refundorderkey
            where refundorder.saleorderkey=%s"""
        values = [(saleorderkey)]
        try:
            cursor2 = mysql.connection.cursor()
            cursor2.execute(sqlst, values)
            refundedquantity = cursor2.fetchone()

            if refundedquantity[0] is None:
                totalrefundedquantity=0
            else:
                totalrefundedquantity=int(refundedquantity[0])
        except Exception as err:
            print (err)

        # print(totalsoldquantity)
        # print(totalrefundedquantity)


        if int(totalrefundedquantity)<int(totalsoldquantity):
            status = 'Y'
        else:
            status = 'N'
    return status





@app.route('/getrefundorderdetails', methods=['GET', 'POST'])
def getrefundorderdetails():
    if 'usersessionid' in session:
        if request.method=='POST':
            refundorderkey=request.form['refundorderkey']
            cursor = mysql.connection.cursor(cursorclass=MySQLdb.cursors.DictCursor)
            sqlst = """ select refundorder.refundorderkey, refundorderdetail.refundorderdetailkey  , refundorderdetail.productkey, 
                        product.barcode ,  refundorderdetail.productname, quantity, 
                        refundorderdetail.saleprice, linetotal from refundorder
                        left join refundorderdetail on refundorder.refundorderkey=refundorderdetail.refundorderkey 
                        left join product on refundorderdetail.productkey=product.productkey 
                        where refundorder.refundorderkey=%s"""
            values = [(refundorderkey)]
            cursor.execute(sqlst, values)
            saleorderdetails = cursor.fetchall()
            return json.dumps(saleorderdetails, cls=DecimalEncoder)
    else:
        return redirect (url_for('login'))








@app.route('/getsoldproductquantity', methods=['GET', 'POST'])
def getsoldproductquantity():
    loginform=LoginForm(request.form)
    myrefundform=RefundForm(request.form)
    if 'usersessionid' in session:
        if request.method=='POST':
            saleorderkey=request.form['saleorderkey']
            barcode=request.form['barcode']
            cursor = mysql.connection.cursor()
            sqlst = """ select  SUM(quantity) as soldquantity
             from `pos`.saleorder
                        left join saleorderdetail on saleorder.saleorderkey=saleorderdetail.saleorderkey 
                        left join product on saleorderdetail.productkey=product.productkey 
                        where saleorder.saleorderkey=%s and saleorderdetail.barcode=%s"""
            values = [(saleorderkey), (barcode)]
            cursor.execute(sqlst, values)
            productsoldquantity = cursor.fetchall()

            return jsonify(productsoldquantity)
        else:
            return render_template('accounts/refund2.html', form=myrefundform)

    else:
        return redirect (url_for('login'))




@app.route('/searchsaleorders', methods=['GET','POST'])
def searchsaleorders():
    mysaleordersearchform=SaleOrderSearchForm(request.form)
    if 'usersessionid' in session:
        cursor = mysql.connection.cursor()
        cursor.execute("select brandkey, brandname from brand union all select 0, 'Select Brand' order by brandkey ")
        allbrands = cursor.fetchall()
        mysaleordersearchform.brandname.choices = allbrands

        cursor.execute("select vendorkey, vendorname from vendor union all select 0, 'Select Vendor' order by vendorkey ")
        allvendors = cursor.fetchall()
        mysaleordersearchform.vendorname.choices = allvendors

        cursor.execute(
            "select categorykey, categoryname from category union all select 0, 'Select Category' order by categorykey ")
        allcategories = cursor.fetchall()
        mysaleordersearchform.categoryname.choices = allcategories

        cursor.execute(
            "select customerkey, customername from customer union all select 0, 'Select Customer' order by customerkey ")
        allcustomers = cursor.fetchall()
        mysaleordersearchform.customername.choices = allcustomers



        if request.method=='POST':
            startdate=request.form['startdate']
            enddate = request.form['enddate']
            categorykey= request.form['categoryname']
            vendorkey = request.form['vendorname']
            brandkey = request.form['brandname']
            customerkey = request.form['customername']
            barcode = request.form['barcode']
            productname = request.form['productname']

            conditions = ' where saleorder.storekey=%s and poskey=%s  '

            if (len(startdate) > 0):
                conditions = conditions + " and date(saleorderdate) >= date('" + startdate + "')"

            if (len(enddate) > 0):
                conditions = conditions + " and date(saleorderdate) <= date('" + enddate + "')"

            if (int(categorykey) > 0):
                conditions = conditions + " and categorykey = '" + categorykey + "'"

            if (int(customerkey) > 0):
                conditions = conditions + " and saleorder.customerkey = '" + customerkey + "'"

            if (int(vendorkey) > 0):
                conditions = conditions + " and vendorkey = '" + vendorkey + "'"

            if (int(brandkey) > 0):
                conditions = conditions + " and product.brandkey = '" + brandkey + "'"

            if (len(productname)>0) :
                conditions = conditions + " and saleorderdetail.productname = '" + productname + "'"

            if (len(barcode)>0) :
                conditions = conditions + " and saleorderdetail.barcode = '" + barcode + "'"


            print (conditions)

            cursor=mysql.connection.cursor(cursorclass=MySQLdb.cursors.DictCursor)
            sqlst="""select distinct customername, saleorder.saleorderkey, saleorder.saleorderdate, saleorder.saleordertotal 
            from saleorder left join saleorderdetail on saleorder.saleorderkey=saleorderdetail.saleorderkey 
            left join product on saleorderdetail.productkey=product.productkey
            left join customer on saleorder.customerkey=customer.customerkey
            """ + conditions
            values=[(session['storekey']), (session['poskey'])]
            # print (values)

            cursor.execute(sqlst, values)

            productdetails=cursor.fetchall()

            # return jsonify(productdetails)

            return render_template('accounts/saleordersearch.html', form=mysaleordersearchform ,productdetails=productdetails)

        if request.method=='GET':
            cursor=mysql.connection.cursor(cursorclass=MySQLdb.cursors.DictCursor)
            sqlst="""select * from saleorder left join customer on saleorder.customerkey=customer.customerkey
            where saleorder.storekey=%s and poskey=%s
            order by saleorderdate, saleorderkey"""
            values=[(session['storekey']), (session['poskey'])]
            cursor.execute(sqlst, values)
            productdetails=cursor.fetchall()
            # return jsonify(productdetails)
            return render_template('accounts/saleordersearch.html', form=mysaleordersearchform ,productdetails=productdetails)
    else:
        return redirect (url_for('login'))







@app.route('/searchgoodsissues', methods=['GET','POST'])
def searchgoodsissues():
    mygoodsissuesearchform=GoodsIssueSearchForm(request.form)
    if 'usersessionid' in session:
        cursor = mysql.connection.cursor()
        cursor.execute("select brandkey, brandname from brand union all select 0, 'Select Brand' order by brandkey ")
        allbrands = cursor.fetchall()
        mygoodsissuesearchform.brandname.choices = allbrands

        cursor.execute("select vendorkey, vendorname from vendor union all select 0, 'Select Vendor' order by vendorkey ")
        allvendors = cursor.fetchall()
        mygoodsissuesearchform.vendorname.choices = allvendors

        cursor.execute(
            "select categorykey, categoryname from category union all select 0, 'Select Category' order by categorykey ")
        allcategories = cursor.fetchall()
        mygoodsissuesearchform.categoryname.choices = allcategories

        cursor.execute(
            "select warehousekey, warehousename from warehouse union all select 0, 'Select Warehouse' order by warehousekey ")
        allwarehouses = cursor.fetchall()
        mygoodsissuesearchform.warehousename.choices = allwarehouses



        if request.method=='POST':
            startdate=request.form['startdate']
            enddate = request.form['enddate']
            categorykey= request.form['categoryname']
            warehousekey = request.form['warehousename']
            vendorkey = request.form['vendorname']
            brandkey = request.form['brandname']
            barcode = request.form['barcode']
            productname = request.form['productname']

            conditions = ' where 1=1  '

            if (len(startdate) > 0):
                conditions = conditions + " and date(goodsissuedate) >= date('" + startdate + "')"

            if (len(enddate) > 0):
                conditions = conditions + " and date(goodsissuedate) <= date('" + enddate + "')"

            if (int(categorykey) > 0):
                conditions = conditions + " and categorykey = '" + categorykey + "'"

            if (int(vendorkey) > 0):
                conditions = conditions + " and vendorkey = '" + vendorkey + "'"

            if (int(warehousekey) > 0):
                conditions = conditions + " and goodsissue.warehousekey = '" + warehousekey + "'"

            if (int(brandkey) > 0):
                conditions = conditions + " and product.brandkey = '" + brandkey + "'"

            if (len(productname)>0) :
                conditions = conditions + " and goodsissuedetail.productname = '" + productname + "'"

            if (len(barcode)>0) :
                conditions = conditions + " and goodsissuedetail.barcode = '" + barcode + "'"


            print (conditions)

            cursor=mysql.connection.cursor(cursorclass=MySQLdb.cursors.DictCursor)
            sqlst="""select distinct  warehousename,goodsissue.goodsissuekey, goodsissue.goodsissuedate, goodsissue.goodsissuetotal 
            from goodsissue left join goodsissuedetail on goodsissue.goodsissuekey=goodsissuedetail.goodsissuekey 
            left join warehouse on goodsissue.warehousekey=warehouse.warehousekey
            left join product on goodsissuedetail.productkey=product.productkey
            """ + conditions
            cursor.execute(sqlst)
            productdetails=cursor.fetchall()

            # return jsonify(productdetails)

            return render_template('accounts/goodsissuesearch.html', form=mygoodsissuesearchform ,productdetails=productdetails)

        if request.method=='GET':
            cursor=mysql.connection.cursor(cursorclass=MySQLdb.cursors.DictCursor)
            sqlst="""select * from goodsissue 
            left join warehouse on goodsissue.warehousekey=warehouse.warehousekey
            order by goodsissuedate, goodsissuekey"""
            cursor.execute(sqlst)
            productdetails=cursor.fetchall()
            # return jsonify(productdetails)
            return render_template('accounts/goodsissuesearch.html', form=mygoodsissuesearchform ,productdetails=productdetails)
    else:
        return redirect (url_for('login'))






@app.route('/searchgrpos', methods=['GET','POST'])
def searchgrpos():
    mygrposearchform=GRPOSearchForm(request.form)
    if 'usersessionid' in session:
        cursor = mysql.connection.cursor()
        cursor.execute("select brandkey, brandname from brand union all select 0, 'Select Brand' order by brandkey ")
        allbrands = cursor.fetchall()
        mygrposearchform.brandname.choices = allbrands

        cursor.execute("select vendorkey, vendorname from vendor union all select 0, 'Select Vendor' order by vendorkey ")
        allvendors = cursor.fetchall()
        mygrposearchform.vendorname.choices = allvendors

        cursor.execute(
            "select categorykey, categoryname from category union all select 0, 'Select Category' order by categorykey ")
        allcategories = cursor.fetchall()
        mygrposearchform.categoryname.choices = allcategories

        if request.method=='POST':
            startdate=request.form['startdate']
            enddate = request.form['enddate']
            categorykey= request.form['categoryname']
            vendorkey = request.form['vendorname']
            brandkey = request.form['brandname']
            barcode = request.form['barcode']
            productname = request.form['productname']

            conditions = ' where grpo.warehousekey=%s   '

            if (len(startdate) > 0):
                conditions = conditions + " and date(receiptdate) >= date('" + startdate + "')"

            if (len(enddate) > 0):
                conditions = conditions + " and date(receiptdate) <= date('" + enddate + "')"

            if (int(categorykey) > 0):
                conditions = conditions + " and product.categorykey = '" + categorykey + "'"

            if (int(vendorkey) > 0):
                conditions = conditions + " and product.vendorkey = '" + vendorkey + "'"

            if (int(brandkey) > 0):
                conditions = conditions + " and product.brandkey = '" + brandkey + "'"

            if (len(productname)>0) :
                conditions = conditions + " and grpodetail.productname = '" + productname + "'"

            if (len(barcode)>0) :
                conditions = conditions + " and grpodetail.barcode = '" + barcode + "'"


            # print (conditions)

            cursor=mysql.connection.cursor(cursorclass=MySQLdb.cursors.DictCursor)
            sqlst="""select distinct vendorname, warehousename, grpo.grpokey, receiptdate from grpo left join grpodetail on grpo.grpokey=grpodetail.grpokey 
            left join product on grpodetail.productkey=product.productkey
            left join warehouse on grpo.warehousekey=warehouse.warehousekey
            left join vendor on grpo.vendorkey=vendor.vendorkey
            """ + conditions
            values=[(session['warehousekey'])]
            # print (values)

            cursor.execute(sqlst, values)

            productdetails=cursor.fetchall()

            # return jsonify(productdetails)

            return render_template('accounts/grposearch.html', form=mygrposearchform ,productdetails=productdetails)

        if request.method=='GET':
            cursor=mysql.connection.cursor(cursorclass=MySQLdb.cursors.DictCursor)
            sqlst="""select * from grpo 
            left join warehouse on grpo.warehousekey=warehouse.warehousekey
            left join vendor on grpo.vendorkey=vendor.vendorkey
            where grpo.warehousekey=%s 
            order by receiptdate, grpokey"""
            values=[(session['warehousekey'])]
            # print (values)
            cursor.execute(sqlst, values)
            productdetails=cursor.fetchall()
            # return jsonify(productdetails)
            return render_template('accounts/grposearch.html', form=mygrposearchform ,productdetails=productdetails)
    else:
        return redirect (url_for('login'))





@app.route('/searchgoodsreceipts', methods=['GET','POST'])
def searchgoodsreceipts():
    mygoodsreceiptsearchform=GoodsReceiptSearchForm(request.form)
    if 'usersessionid' in session:
        cursor = mysql.connection.cursor()
        cursor.execute("select brandkey, brandname from brand union all select 0, 'Select Brand' order by brandkey ")
        allbrands = cursor.fetchall()
        mygoodsreceiptsearchform.brandname.choices = allbrands

        cursor.execute("select vendorkey, vendorname from vendor union all select 0, 'Select Vendor' order by vendorkey ")
        allvendors = cursor.fetchall()
        mygoodsreceiptsearchform.vendorname.choices = allvendors

        cursor.execute(
            "select categorykey, categoryname from category union all select 0, 'Select Category' order by categorykey ")
        allcategories = cursor.fetchall()
        mygoodsreceiptsearchform.categoryname.choices = allcategories

        cursor.execute(
            "select warehousekey, warehousename from warehouse union all select 0, 'Select Warehouse' order by warehousekey ")
        allwarehouses = cursor.fetchall()
        mygoodsreceiptsearchform.warehousename.choices = allwarehouses

        if request.method=='POST':
            startdate=request.form['startdate']
            enddate = request.form['enddate']
            categorykey= request.form['categoryname']
            vendorkey = request.form['vendorname']
            brandkey = request.form['brandname']
            barcode = request.form['barcode']
            productname = request.form['productname']
            warehousekey = request.form['warehousename']
            conditions = ' where 1=1   '

            if (len(startdate) > 0):
                conditions = conditions + " and date(receiptdate) >= date('" + startdate + "')"

            if (len(enddate) > 0):
                conditions = conditions + " and date(receiptdate) <= date('" + enddate + "')"

            if (int(categorykey) > 0):
                conditions = conditions + " and product.categorykey = '" + categorykey + "'"

            if (int(vendorkey) > 0):
                conditions = conditions + " and product.vendorkey = '" + vendorkey + "'"

            if (int(brandkey) > 0):
                conditions = conditions + " and product.brandkey = '" + brandkey + "'"

            if (int(warehousekey) > 0):
                conditions = conditions + " and goodsreceipt.warehousekey = '" + warehousekey + "'"

            if (len(productname)>0) :
                conditions = conditions + " and goodsreceiptdetail.productname = '" + productname + "'"

            if (len(barcode)>0) :
                conditions = conditions + " and goodsreceiptdetail.barcode = '" + barcode + "'"


            # print (conditions)

            cursor=mysql.connection.cursor(cursorclass=MySQLdb.cursors.DictCursor)
            sqlst="""select distinct warehousename, goodsreceipt.goodsreceiptkey, receiptdate from goodsreceipt
             left join goodsreceiptdetail on goodsreceipt.goodsreceiptkey=goodsreceiptdetail.goodsreceiptkey 
            left join product on goodsreceiptdetail.productkey=product.productkey
            left join warehouse on goodsreceipt.warehousekey=warehouse.warehousekey
            """ + conditions


            cursor.execute(sqlst)

            productdetails=cursor.fetchall()

            # return jsonify(productdetails)

            return render_template('accounts/goodsreceiptsearch.html', form=mygoodsreceiptsearchform ,productdetails=productdetails)

        if request.method=='GET':
            cursor=mysql.connection.cursor(cursorclass=MySQLdb.cursors.DictCursor)
            sqlst="""select * from goodsreceipt 
            left join warehouse on goodsreceipt.warehousekey=warehouse.warehousekey
            order by receiptdate, goodsreceiptkey"""

            # print (values)
            cursor.execute(sqlst)
            productdetails=cursor.fetchall()
            # return jsonify(productdetails)
            return render_template('accounts/goodsreceiptsearch.html', form=mygoodsreceiptsearchform ,productdetails=productdetails)
    else:
        return redirect (url_for('login'))






@app.route('/dailysalereport', methods=['GET','POST'])
def dailysalereport():
    mydailysalereportform=DailySaleReportForm(request.form)
    if 'usersessionid' in session:

        cursor = mysql.connection.cursor()
        cursor.execute("select storekey, storename from store union all select 0, 'Select Store' order by storekey ")
        allstores = cursor.fetchall()
        mydailysalereportform.storename.choices = allstores

        cursor.execute("select poskey, posname from pos union all select 0, 'Select POS' order by poskey ")
        allposs = cursor.fetchall()
        mydailysalereportform.posname.choices = allposs

        if request.method=='POST':
            startdate=request.form['startdate']
            enddate = request.form['enddate']
            storekey= request.form['storename']
            poskey = request.form['posname']

            conditions = ' where 1=1   '

            if (len(startdate) > 0):
                conditions = conditions + " and date(saleorderdate) >= date('" + startdate + "')"

            if (len(enddate) > 0):
                conditions = conditions + " and date(saleorderdate) <= date('" + enddate + "')"

            if (int(storekey) > 0):
                conditions = conditions + " and saleorder.storekey = '" + storekey + "'"

            if (int(poskey) > 0):
                conditions = conditions + " and saleorder.poskey = '" + poskey + "'"

            cursor = mysql.connection.cursor(cursorclass=MySQLdb.cursors.DictCursor)

            # print (conditions)

            sqlst = """
                  select saleorderdate ,store.storename, pos.posname , product.productname, product.barcode, 
                  categoryname, brandname, vendorname , SUM(quantity)soldquantity, sum(linetotal)linetotal  
                  from saleorder 
                  left join saleorderdetail on saleorder.saleorderkey=saleorderdetail.saleorderkey
                  left join product on saleorderdetail.productkey=product.productkey
                  left join brand on product.brandkey=brand.brandkey
                  left join category on product.categorykey=category.categorykey
                  left join vendor on product.vendorkey=vendor.vendorkey
                  left join store on saleorder.storekey=store.storekey
                  left join pos on saleorder.poskey=pos.poskey""" + conditions

            sqlst = sqlst +  """ group by saleorderdate , store.storename, pos.posname , product.productname,
                   product.barcode, categoryname, brandname, vendorname 
                  """

            cursor.execute(sqlst)
            productdetails=cursor.fetchall()



            if request.form['btnview']=='btnprint':
                options = {
                    "enable-local-file-access": None
                }
                rendered =  render_template('accounts/reportprint.html', form=mydailysalereportform ,productdetails=productdetails)
                pdf = pdfkit.from_string(rendered, False,  options=options)
                response=make_response(pdf)
                response.headers['Content-Type']='application/pdf'
                response.headers['Content-Disposition'] = 'attachment; filename=output.pdf'
                return response

            if request.form['btnview'] == 'btnview':
                return render_template('accounts/dailysalereport.html', form=mydailysalereportform, productdetails=productdetails)



        if request.method=='GET':
            # cursor=mysql.connection.cursor(cursorclass=MySQLdb.cursors.DictCursor)
            # sqlst="""select * from goodsreceipt
            # left join warehouse on goodsreceipt.warehousekey=warehouse.warehousekey
            # order by receiptdate, goodsreceiptkey"""
            #
            # # print (values)
            # cursor.execute(sqlst)
            # productdetails=cursor.fetchall()
            # # return jsonify(productdetails)
            return render_template('accounts/dailysalereport.html', form=mydailysalereportform )
    else:
        return redirect (url_for('login'))








@app.route('/logout', methods=['GET','POST'])
def logout():
    session.pop('usersessionid')
    session.pop('userkey')
    session.pop('storekey')
    session.pop('poskey')
    session.pop('warehousekey')
    session.pop('username')
    session.pop('storename')
    session.pop('posname')

    return redirect(url_for('login'))




if __name__ == '__main__':
    app.run(debug=True)
