To run this project on your local machine follow these steps
	1. Clone git repository into your machine
	2. Open any IDE of your choice then open the cloned folder
	3. Make sure postgreSQL is installed successfully on your machine then create a database named "webproject" using 
	   pgadmin4 tool and also sync the password in setting.py file (In database snippet of settings.py file)
	4. Go to terminal in IDE / cmd then run 
		4.1. 'python manage.py collectstatic'
		4.2. 'python manage.py makemigrations'
		4.3. 'python manage.py migrate'
	5. Now run 'python manage.py runserver'
	6. Then enter search for 'http://127.0.0.1:8000/' in your browser

If that sounds a headache, just browse for 'http://split-wiser.herokuapp.com/' and start using it.
