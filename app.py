from flask import Flask, redirect, url_for, render_template

app = Flask(__name__)

@app.route("/")
def homepage():
    return redirect("/index/")

@app.route("/index/")
def index():
    return render_template("index.html", CurrentPage="index", Meow = False)

@app.route("/map/")
def map():
    return render_template("mmu.html", CurrentPage="map")

@app.route("/meow/")
def rick():
    Meow = True
    return render_template("index.html", Meow = True)

if __name__ == "__main__":
    app.run(debug=True)