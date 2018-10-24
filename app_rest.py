from flask import Flask, render_template, send_from_directory, abort, request, session, redirect, send_file, url_for, jsonify
import flask
import os
import tasho
import settings
import secrets

app = Flask(__name__, static_url_path='')
app.debug = settings.debug
db = tasho.Database.open("links", True)
linkTable = db.table.Links

@app.route("/")
def index():
    return send_from_directory('templates', "index.html")


@app.route("/new", methods=["POST"])
def newLink():
    data = request.json
    if not data:
        data = request.form

    if settings.password and data.get("password") != settings.password:
        return jsonify({"error": "Invalid password!"})

    if not data.get("link", None):
        return jsonify({"error": "No link to route to."})

    shortlink = data.get("shortlink", None)
    if linkTable.get(shortlink):
        return jsonify({"error": "Shortlink is already assigned."})

    if request.host in data["link"]:
        return jsonify({"error": "Can't shorten this link."})

    if not (data["link"].startswith("https://") or data["link"].startswith("http://")):
        data["link"] = "https://" + data["link"]

    link = linkTable.insert(shortlink if shortlink else secrets.token_urlsafe(6), {
        "link": data.get("link", settings.noLink),
        "views": 0
    })

    return jsonify({"ok": request.url_root.replace("http://", "https://")+link._id})


@app.route("/g/<query>")
def google(query):
    return redirect(f"https://google.com/search?q={query}")    

@app.route("/delete", methods=["POST"])
def delete():
    data = request.json
    if settings.deletePassword and data.get("password") != settings.deletePassword:
        return jsonify({"error": "Invalid password!"})

    link = linkTable.get(data['shortlink'])
    link.delete()
    return jsonify({"ok": link._id})


@app.route("/<shortlink>/stats")
def stats(shortlink):
    link = linkTable.get(shortlink)
    if not link:
        return jsonify({"error": "Link not found or probably deleted."})

    return jsonify({"views": link.views})

@app.route("/<shortlink>")
def resolve(shortlink):
    link = linkTable.get(shortlink)
    if not link:
        return jsonify({"error": "Link not found or probably deleted."})
    link.views += 1
    link.save()
    return redirect(link.link)
    #return jsonify({"redirect": link.link})


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 2500))
    app.run(host='0.0.0.0', port=port)
