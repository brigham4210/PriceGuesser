from flask import Flask, render_template, request, session, redirect, url_for
from Zillow.url import Url
from Zillow.property import Property
from Zillow.information import Information
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/generate', methods=['POST'])
def generate():
    # Get form inputs
    state = request.form.get('state')
    bed_min = request.form.get('bed_min', type=int)
    bed_max = request.form.get('bed_max', type=int)
    bath_min = request.form.get('bath_min', type=int)
    bath_max = request.form.get('bath_max', type=int)
    
    # Store search criteria in session
    session['search_criteria'] = {
        'state': state,
        'bed_min': bed_min,
        'bed_max': bed_max,
        'bath_min': bath_min,
        'bath_max': bath_max
    }
    
    # Create URL and get random property
    url = Url(state=state, bed_min=bed_min, bed_max=bed_max, 
              bath_min=bath_min, bath_max=bath_max)
    property_obj = Property(url)
    property_url = property_obj.get_random_property_url()
    
    # Get property information
    info = Information(property_url)
    address, price, beds, baths, sqft, land_area, year_built, image_urls = info.get_info()
    
    # Store in session
    session['property_url'] = property_url
    session['address'] = address
    session['price'] = price
    session['beds'] = beds
    session['baths'] = baths
    session['sqft'] = sqft
    session['land_area'] = land_area
    session['year_built'] = year_built
    session['image_urls'] = image_urls
    session['guessed'] = False
    
    return redirect(url_for('game'))


@app.route('/game')
def game():
    if 'address' not in session:
        return redirect(url_for('index'))
    
    return render_template('game.html',
                         address=session.get('address'),
                         beds=session.get('beds'),
                         baths=session.get('baths'),
                         sqft=session.get('sqft'),
                         land_area=session.get('land_area'),
                         year_built=session.get('year_built'),
                         image_urls=session.get('image_urls'),
                         guessed=session.get('guessed', False),
                         price=session.get('price') if session.get('guessed') else None,
                         user_guess=session.get('user_guess'),
                         property_url=session.get('property_url'))


@app.route('/guess', methods=['POST'])
def guess():
    user_guess = request.form.get('guess')
    session['user_guess'] = user_guess
    session['guessed'] = True
    return redirect(url_for('game'))


@app.route('/generate_again')
def generate_again():
    # Use stored search criteria to get another property
    if 'search_criteria' not in session:
        return redirect(url_for('index'))
    
    criteria = session['search_criteria']
    url = Url(state=criteria['state'], 
              bed_min=criteria['bed_min'], 
              bed_max=criteria['bed_max'],
              bath_min=criteria['bath_min'], 
              bath_max=criteria['bath_max'])
    property_obj = Property(url)
    property_url = property_obj.get_random_property_url()
    
    # Get property information
    info = Information(property_url)
    address, price, beds, baths, sqft, land_area, year_built, image_urls = info.get_info()
    
    # Update session with new property
    session['property_url'] = property_url
    session['address'] = address
    session['price'] = price
    session['beds'] = beds
    session['baths'] = baths
    session['sqft'] = sqft
    session['land_area'] = land_area
    session['year_built'] = year_built
    session['image_urls'] = image_urls
    session['guessed'] = False
    session.pop('user_guess', None)
    
    return redirect(url_for('game'))


@app.route('/reset')
def reset():
    session.clear()
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
