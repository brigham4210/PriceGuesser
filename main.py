from flask import Flask, render_template, request, session, redirect, url_for
from Zillow.url import Url
from Zillow.property import Property
from Zillow.information import Information
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)


def _get_random_property_url_with_fallback(criteria):
    # First try the user's exact criteria, then retry once with relaxed filters.
    attempts = [
        criteria,
        {
            'state': criteria.get('state'),
            'bed_min': None,
            'bed_max': None,
            'bath_min': None,
            'bath_max': None,
        }
    ]

    for attempt in attempts:
        url = Url(state=attempt['state'],
                  bed_min=attempt['bed_min'],
                  bed_max=attempt['bed_max'],
                  bath_min=attempt['bath_min'],
                  bath_max=attempt['bath_max'])
        property_obj = Property(url)
        try:
            return property_obj.get_random_property_url()
        except ValueError:
            continue

    raise ValueError(
        "No properties found for your filters or broad state search. Try another state."
    )


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

    try:
        property_url = _get_random_property_url_with_fallback(session['search_criteria'])
    except ValueError as err:
        return render_template('index.html', error=str(err))

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

    # Calculate difference if guessed
    difference = None
    if session.get('guessed'):
        try:
            # Extract numeric value from user guess
            user_guess_str = session.get('user_guess', '').replace('$', '').replace(',', '').strip()
            user_guess_num = float(user_guess_str)

            # Extract numeric value from actual price
            actual_price_str = session.get('price', '').replace('$', '').replace(',', '').strip()
            actual_price_num = float(actual_price_str)

            # Calculate difference
            difference = user_guess_num - actual_price_num
        except (ValueError, AttributeError):
            difference = None

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
                           property_url=session.get('property_url'),
                           difference=difference)


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
    try:
        property_url = _get_random_property_url_with_fallback(criteria)
    except ValueError as err:
        return render_template('index.html', error=str(err))

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
