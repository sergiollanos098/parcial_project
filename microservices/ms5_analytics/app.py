from flask import Flask, jsonify
app = Flask(__name__)
@app.route('/analytics/exams_by_specialty')
def exams_by_specialty():
    # mocked aggregated result - in real case use Athena queries
    data = [{"specialty":"spec0","count":120},{"specialty":"spec1","count":98},{"specialty":"spec2","count":140}]
    return jsonify(data)

@app.route('/analytics/viewsample')
def viewsample():
    return jsonify({"view":"sample","rows":10})

if __name__=='__main__':
    app.run(host='0.0.0.0', port=5005)
