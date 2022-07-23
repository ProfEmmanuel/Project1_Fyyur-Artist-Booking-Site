#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from datetime import datetime
from models import db, Venue, Artist, Show
from flask_migrate import Migrate

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db.app = app
db.init_app(app)

Migrate(app, db)

# TODO: connect to a local postgresql database

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

def get_current_time():
  # return datetime.now().strftime('%Y-%m-%d %H:%M:%S:%f')
  return str(datetime.now())

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # DONE: replace with real venues data.
  #       num_upcoming_shows should be aggregated based on number of upcoming shows per venue.
  current_time = get_current_time()
  venues = Venue.query.group_by(Venue.city, Venue.state, 
          Venue.id, Venue.name).all()
  parts = []
  data = []

  for v in venues:
    upcoming_show = v.shows.filter(current_time < Show.start_time)
    if v.name not in parts:
      data.append({'city': v.city, 'state':v.state, 
        'venues':[{'id':v.id, 'name': v.name, 
        'num_upcoming_shows': len(upcoming_show.all())}]})
    else:
      parts.append(v.name)

  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # DONE: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  search = request.form['search_term']
  venues = Venue.query.order_by(Venue.id).filter(Venue.name.ilike('%'+search+'%')).all()
  count = len(venues)
  current_time = get_current_time()
  response = {"count" : count, 'data':[]}
  for venue in venues:
    upcoming_show = venue.shows.filter(Show.start_time > current_time)
    response["data"].append({
            "id": venue.id,
            "name": venue.name,
            "num_upcoming_shows" : upcoming_show
        })

  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # DONE: replace with real venue data from the venues table, using venue_id
  current_time = get_current_time()
  venue = Venue.query.filter(Venue.id == venue_id).first()
  upcoming_shows = venue.shows.filter(Show.start_time > current_time).all()
  # upcoming_shows = venue.shows.filter(Show.start_time > current_time).all()
  past_shows = venue.shows.filter(Show.start_time < current_time).all()

  past_shows_list = [{
    'artist_id': show.artist.id,
    'artist_name': show.artist.name,
    'artist_image_link': show.artist.image_link,
    'start_time': str(show.start_time)
    } for show in past_shows]

  upcoming_shows_list = [{
    'artist_id': show.artist.id,
    'artist_name': show.artist.name,
    'artist_image_link': show.artist.image_link,
    'start_time': str(show.start_time)
    } for show in upcoming_shows] 


  data={
    "id": venue.id,
    "name": venue.name,
    "genres": venue.genres.split(','),
    "address": venue.address,
    "city": venue.city,
    "state": venue.state,
    "phone": venue.phone,
    "website": venue.website,
    "facebook_link": venue.facebook_link,
    "seeking_talent": venue.seeking_talent,
    "seeking_description": venue.seeking_description,
    "image_link": venue.image_link,
    "upcoming_shows": upcoming_shows_list,
     "past_shows": past_shows_list,
    "past_shows_count": len(past_shows),
    "upcoming_shows_count": len(upcoming_shows)
  }

  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # DONE: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  form = VenueForm()
  body = request.form.to_dict()
  # print("This is body : ->  ", body)
  # print('Genres : ->', request.form.getlist('genres'))
  name = body['name']
  if form.validate_on_submit():
    try:
      venue = Venue(name= body.get('name'),
        city= body['city'],
        state = body.get('state'),
        address = body.get('address'),
        phone = body.get('phone'),
        image_link = body.get('image_link'),
        facebook_link = body.get('facebook_link'),
        genres = ",".join(request.form.getlist('genres')), # TODO: Getting all genres
        website = body.get('website'),
        seeking_talent = bool(body.get('seeking_talent')),
        seeking_description = body.get('seeking_description')
        )
      db.session.add(venue)
      db.session.commit()
      # on successful db insert, flash success
      flash('Venue ' + venue.name + ' was successfully listed!')
    except :
      db.session.rollback()
      flash('An error occurred. Venue ' + name +' could not be listed.')
    # DONE: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  else:
    for field, message in form.errors.items():
      flash(field + ' - ' + str(message), 'danger')
  return render_template('pages/home.html', form=form)

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
  try:
    Venue.query.filter(Venue.id == venue_id).delete()
    db.session.commit()
    flash('Venue number ' + venue_id + ' was successfully deleted!')
  except:
    db.session.rollback()
    flash('An error occurred. Venue number' + venue_id + ' could not be deleted.')
  finally:
    db.session.close()
  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  return None

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # DONE: replace with real data returned from querying the database
  artists = Artist.query.all()
  data = [{"id": a.id, "name": a.name}
               for a in artists]
 
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # DONE: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".

  search = request.form['search_term']
  artists = Artist.query.order_by(Artist.id).filter(Artist.name.ilike('%'+search+'%')).all()
  count = len(artists)
  current_time = get_current_time()
  response = {"count" : count, 'data':[]}
  for artist in artists:
    upcoming_shows = artist.shows.filter(Show.start_time > current_time).all()
    response["data"].append({
            "id": artist.id,
            "name": artist.name,
            "num_upcoming_shows" : len(upcoming_shows)
        })
  
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the artist page with the given artist_id
  # TODO: replace with real artist data from the artist table, using artist_id

  current_time = get_current_time()
  artist = Artist.query.filter(Artist.id == artist_id).first()
  upcoming_shows = artist.shows.filter(Show.start_time > current_time).all()

  past_shows = artist.shows.filter(Show.start_time < current_time).all()

  past_shows_list = [{
    'venue_id': show.venue.id,
    'venue_name': show.venue.name,
    'venue_image_link': show.venue.image_link,
    'start_time': str(show.start_time)
    } for show in past_shows]

  upcoming_shows_list = [{
    'venue_id': show.venue.id,
    'venue_name': show.venue.name,
    'venue_image_link': show.venue.image_link,
    'start_time': str(show.start_time)
    } for show in upcoming_shows]


  data={
    "id": artist.id,
    "name": artist.name,
    "genres": artist.genres.split(','),
    "city": artist.city,
    "state": artist.state,
    "phone": artist.phone,
    "website": artist.website,
    "facebook_link": artist.facebook_link,
    "seeking_venue": artist.seeking_venue,
    "seeking_description": artist.seeking_description,
    "image_link": artist.image_link,
    "past_shows" : past_shows_list,
    "upcoming_shows": upcoming_shows_list,
    "past_shows_count": len(past_shows),
    "upcoming_shows_count": len(upcoming_shows),
  }


  
  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()

  get_artist = Artist.query.filter(Artist.id == artist_id).one_or_none()

  if get_artist:
    artist={
      "id": get_artist.id,
      "name": get_artist.name,
      "genres": get_artist.genres.split(','),
      "city": get_artist.city,
      "state": get_artist.state,
      "phone": get_artist.phone,
      "website": get_artist.website,
      "facebook_link": get_artist.facebook_link,
      "seeking_venue": get_artist.seeking_venue,
      "seeking_description": get_artist.seeking_description,
      "image_link": get_artist.image_link
    }
  else:
    artist = {}
  # DONE: populate form with fields from artist with ID <artist_id>
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # DONE: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes

  body = request.form.to_dict()

  artist = Artist.query.filter(Artist.id == artist_id).one_or_none()
  try:

    if artist:
      artist.name = body.get('name')
      artist.genres = ','.join(body.get('genres'))
      artist.city = body.get('city')
      artist.state = body.get('state')
      artist.phone = body.get('phone')
      artist.website = body.get('website')
      artist.facebook_link = body.get('facebook_link')
      artist.seeking_venue = body.get('seeking_venue')
      artist.seeking_description = body.get('seeking_description')
      get_artist.image_link = body.get('image_link')

    db.session.commit()
    flash('Artist ' + artist.name + ' was successfully updated!')
  except:
    db.session.rollback()
    flash('')

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()

  get_venue = Venue.query.filter(Venue.id == venue_id).one_or_none()

  venue={
    "id": get_venue.id,
    "name": get_venue.name,
    "genres": get_venue.genres.split(','),
    "address": get_venue.address,
    "city": get_venue.city,
    "state": get_venue.state,
    "phone": get_venue.phone,
    "website": get_venue.website,
    "facebook_link": get_venue.facebook_link,
    "seeking_talent": get_venue.seeking_talent,
    "seeking_description": get_venue.seeking_description,
    "image_link": get_venue.image_link
  }
  # DONE: populate form with values from venue with ID <venue_id>
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # DONE: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  venue = Venue.query.filter(Venue.id == venue_id).one_or_none()
  try:
    if venue:
      venue.name= body.get('name'),
      venue.city= body['city'],
      venue.state = body.get('state'),
      venue.address = body.get('address'),
      venue.phone = body.get('phone'),
      venue.image_link = body.get('image_link'),
      venue.facebook_link = body.get('facebook_link'),
      venue.genres = ",".join(request.form.getlist('genres')), # DONE: Getting all genres
      venue.website = body.get('website'),
      venue.seeking_talent = bool(body.get('seeking_talent')),
      venue.seeking_description = body.get('seeking_description')

      db.session.commit()
      flash('Venue ' + venue.name + ' was successfully listed!')
  except:
    db.session.rollback()
    flash('An error occurred. Venue ' + venue.name + ' could not be updated.')
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  # DONE: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  form = ArtistForm()
  body = request.form.to_dict()
  name = body['name']
  if form.validate_on_submit():
    try:
      artist = Artist(name= body.get('name'),
        city= body['city'],
        state = body.get('state'),
        phone = body.get('phone'),
        image_link = body.get('image_link'),
        facebook_link = body.get('facebook_link'),
        genres = ",".join(request.form.getlist('genres')), 
        website = body.get('website'),
        seeking_venue = bool(body.get('seeking_venue')),
        seeking_description = body.get('seeking_description')
        )
      db.session.add(artist)
      db.session.commit()
      # on successful db insert, flash success
      flash('Artist ' + artist.name + ' was successfully listed!')
    except Exception as Error:
      db.session.rollback()
      flash('An error occurred. Artist ' + name + '  ' + str(Error) +' could not be listed.')
    finally:
      db.session.close()
  else:
    for field, message in form.errors.items():
      flash(field + ' - ' + str(message), 'danger')

  return render_template('pages/home.html', form=form)


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # DONE: replace with real venues data.
  shows = Show.query.all()

  data = []
  for show in shows:
    data.append({
      'venue_id': show.venue_id,
      'venue_name': show.venue.name,
      'artist_id': show.artist_id,
      'artist_name': show.artist.name,
      'artist_image_link': show.artist.image_link,
      'start_time': str(show.start_time)
      })
  # data=[{
  #   "venue_id": 1,
  #   "venue_name": "The Musical Hop",
  #   "artist_id": 1,
  #   "artist_name": "Guns N Petals",
  #   "artist_image_link": "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80",
  #   "start_time": "2019-05-21T21:30:00.000Z"
  # }, {
  #   "venue_id": 3,
  #   "venue_name": "Park Square Live Music & Coffee",
  #   "artist_id": 5,
  #   "artist_name": "Matt Quevedo",
  #   "artist_image_link": "https://images.unsplash.com/photo-1495223153807-b916f75de8c5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=334&q=80",
  #   "start_time": "2019-06-15T23:00:00.000Z"
  # }, {
  #   "venue_id": 3,
  #   "venue_name": "Park Square Live Music & Coffee",
  #   "artist_id": 6,
  #   "artist_name": "The Wild Sax Band",
  #   "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
  #   "start_time": "2035-04-01T20:00:00.000Z"
  # }, {
  #   "venue_id": 3,
  #   "venue_name": "Park Square Live Music & Coffee",
  #   "artist_id": 6,
  #   "artist_name": "The Wild Sax Band",
  #   "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
  #   "start_time": "2035-04-08T20:00:00.000Z"
  # }, {
  #   "venue_id": 3,
  #   "venue_name": "Park Square Live Music & Coffee",
  #   "artist_id": 6,
  #   "artist_name": "The Wild Sax Band",
  #   "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
  #   "start_time": "2035-04-15T20:00:00.000Z"
  # }]
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # DONE: insert form data as a new Show record in the db, instead

  body = request.form.to_dict()
  try:
    show = Show(
      venue_id=body.get('venue_id'),
      artist_id=body.get('artist_id'),
      start_time=body.get('start_time')
      )
    db.session.add(show)
    db.session.commit()
    # on successful db insert, flash success
    flash('Show was successfully listed!')
  except:
    db.session.rollback()
    flash("An error occurred. Show could not be listed.")
  # DONE: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Show could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  finally:
    db.session.close()
  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
