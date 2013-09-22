def get (params):
    url = ""
    for key, value in params:
        url = url + "&" + key + "=" + value

    return  url