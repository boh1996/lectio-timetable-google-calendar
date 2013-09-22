def get (params):
    url = ""
    for key in params:
        url = url + "&" + key + "=" + params[key]
    return  url