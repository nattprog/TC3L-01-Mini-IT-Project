from flask import Flask, redirect, url_for, render_template

app = Flask(__name__)

@app.route("/")
def RedirectHome():
    return redirect(url_for("home"))

@app.route("/home/")
def home():
    return render_template("index.html", ActivePage="index")

@app.route("/home/<path>")
def floor(path):
    return render_template("index.html", ActivePage="index", ActiveFloor = path)

@app.route("/map/")
def map():
    return render_template("mmu.html", ActivePage="map")

@app.route("/meow/")
def meow():
    return render_template("index.html", ActivePage ="meow", Meow = True)

if __name__ == "__main__":
    app.run(debug=True)