from flask import current_app as app
from flask import request
from datetime import datetime, timedelta
from toolkit import dbAlchemy as db
from toolkit.seo.rank import rank
from toolkit.models import Serp

def query_domain_serp( query, domain, lang, tld):
    if query and domain:
        existing_serp = Serp.query.filter(
            Serp.query_text == query and Serp.domain == domain
        ).all()
        existing_serp_count= Serp.query.filter(
            Serp.query_text == query and Serp.domain == domain
        ).count()
        
        print(existing_serp)
        
        if existing_serp_count > 0:
            print(existing_serp[0])
            if existing_serp[0].begin_date + timedelta(hours=24) < datetime.now():
                print("refresh")
                result = rank(domain, query, lang=lang, tld=tld)
                Serp.update().where(query_text==query and domain==domain).values(begin_date=datetime.now(),url=result["url"], pos=result["pos"])
                return result
            else:
                print("no refresh")
                return {"pos": existing_serp[0].pos, "url": existing_serp[0].url, "query": existing_serp[0].query_text}
        
        all_results_count = Serp.query.order_by(Serp.begin_date.desc()).count()
        if all_results_count >= 5:
            all_results = Serp.query.order_by(Serp.begin_date.desc()).all()
            if all_results[4].begin_date+ timedelta(hours=1) > datetime.now():
                print("Already passed")
                waiting = datetime.now() - all_results[4].begin_date
                secs = 3600 - int(waiting.total_seconds())
                minutes = int(secs / 60) % 60
                return {"limit": "Imposing a limit of 5 query per hour to avoid Google Ban", "waiting_time": str(minutes) + "m " + str(int(secs % 60)) + "s" }   
        
        result = rank(domain, query, lang=lang, tld=tld)
        new_result = Serp(query_text=result["query"],pos=result["pos"], domain=domain, url=result["url"], begin_date=datetime.now() )
        db.session.add(new_result)  # Adds new User record to database
        db.session.commit()
        return result


@app.route('/api/serp')
def find_rank_query():
    query = request.args.get('query')
    domain = request.args.get('domain')
    if domain and query:
        tld = request.args.get('tld')
        lang = request.args.get('lang')
        return query_domain_serp(query,domain, lang, tld)
    else:
        return 'Please input a valid value like this: /api/serp?domain=primates.dev&query=parse api xml response&tld=com&lang=en'