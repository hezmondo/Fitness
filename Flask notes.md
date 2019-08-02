### Linux instructions for installing flask and useful add-ons:

	sudo apt-get install python3-flask

	sudo apt-get install python3-flask-sqlalchemy

	sudo apt-get install python3-flask-dotenv

	sudo apt-get install python3-flask-migrate

	sudo apt-get install python3-flask-login

	sudo apt-get install python3-flask-mail

	sudo apt-get install python3-flask-pymysql

	python3 -m pip install flask-bootstrap

	python3 -m pip install flask-wtf

	python3 -m pip install flask-table

	python3 -m pip install PyJWT
	

### Windows instructions for installing flask and useful add-ons:

	pip install flask

	pip install flask-sqlalchemy

	pip install flask-dotenv

	pip install flask-migrate

	pip install flask-login

	pip install flask-mail

	pip install flask-pymysql

	pip install flask-bootstrap

	pip install flask-wtf

	pip install flask-table
	
	pip install PyJWT
	

### Make micro.py runnable as a Python program, instead of having to type flask run, paste at end:

    if __name__ == '__main__':
        app.run(debug=True, use_debugger=False, use_reloader=False, passthrough_errors=True)
      
### Set up to edit/run/debug in PyCharm:

File > Open ..., select Fitness directory.  That loads it as a project.

Run > Edit Configurations ....  Find the Before launch near bottom of tab, click the green "+" beneath it.

Select desired Browser, for Url enter: http://127.0.0.1:5000/

Now you can run/debug from PyCharm, and it will open a new browser window for your app each time automatically.  Output/debug messages go to PyCharm Console tab.
