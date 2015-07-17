from frontend import app as frontend

if __name__ == '__main__':
    frontend.debug = True
    frontend.run(host='0.0.0.0', port=8001)
