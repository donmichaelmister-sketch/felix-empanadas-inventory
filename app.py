#!/usr/bin/env python3
"""
Inventory management web app.
Simple Flask app for employees to submit bag counts and transfers.
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from database import (
    init_db, add_bag, log_transfer, get_bags, 
    get_inventory_summary, update_bag_location
)
from datetime import datetime
import json
import os

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False
app.secret_key = os.environ.get('SECRET_KEY', 'felix-empanadas-secret-key-2026')

# Simple password (change this to something secure)
ADMIN_PASSWORD = os.environ.get('INVENTORY_PASSWORD', 'empanadas123')

# Initialize database on startup
init_db()

def login_required(f):
    """Decorator to require login."""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page."""
    if request.method == 'POST':
        password = request.form.get('password', '')
        if password == ADMIN_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error='Invalid password')
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logout."""
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    """Home page with nav to forms."""
    return render_template('index.html')

@app.route('/add-bag', methods=['GET', 'POST'])
@login_required
def add_bag_form():
    """Add bag form."""
    if request.method == 'POST':
        try:
            data = request.get_json()
            bag_num = int(data.get('bag_num'))
            flavor = data.get('flavor', '').strip()
            count = int(data.get('count'))
            location = data.get('location', 'Latta Storage')
            
            if not flavor:
                return jsonify({'success': False, 'error': 'Flavor required'}), 400
            
            success = add_bag(bag_num, flavor, count, location)
            if success:
                return jsonify({'success': True, 'message': f'Bag #{bag_num} added'})
            else:
                return jsonify({'success': False, 'error': f'Bag #{bag_num} already exists'}), 400
        
        except ValueError as e:
            return jsonify({'success': False, 'error': f'Invalid input: {e}'}), 400
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    return render_template('add-bag.html')

@app.route('/transfer', methods=['GET', 'POST'])
@login_required
def transfer_form():
    """Log transfer form."""
    if request.method == 'POST':
        try:
            data = request.get_json()
            from_loc = data.get('from_location', '').strip()
            to_loc = data.get('to_location', '').strip()
            bags = data.get('bags', '')
            
            if not from_loc or not to_loc:
                return jsonify({'success': False, 'error': 'From and To locations required'}), 400
            
            # Parse bags (comma-separated)
            bag_list = [int(b.strip()) for b in bags.split(',') if b.strip()]
            if not bag_list:
                return jsonify({'success': False, 'error': 'At least one bag required'}), 400
            
            # Update each bag's location
            for bag_num in bag_list:
                update_bag_location(bag_num, to_loc)
            
            # Log the transfer
            log_transfer(from_loc, to_loc, bag_list)
            
            return jsonify({'success': True, 'message': f'Transfer logged: {len(bag_list)} bags'})
        
        except ValueError as e:
            return jsonify({'success': False, 'error': f'Invalid bag numbers: {e}'}), 400
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    return render_template('transfer.html')

@app.route('/inventory')
@login_required
def inventory():
    """View current inventory."""
    summary = get_inventory_summary()
    bags = get_bags()
    return render_template('inventory.html', summary=summary, bags=bags)

@app.route('/api/bags')
def api_bags():
    """JSON API: get all bags."""
    bags = get_bags()
    return jsonify({
        'bags': [
            {
                'bag_num': row[0],
                'flavor': row[1],
                'date': row[2],
                'count': row[3],
                'location': row[4]
            }
            for row in bags
        ]
    })

@app.route('/api/inventory')
def api_inventory():
    """JSON API: get inventory summary."""
    return jsonify(get_inventory_summary())

@app.route('/api/next-bag-number')
def api_next_bag_number():
    """JSON API: get the next available bag number."""
    bags = get_bags()
    if not bags:
        return jsonify({'next_number': 1})
    
    max_num = max(int(bag[0]) for bag in bags)
    return jsonify({'next_number': max_num + 1})

if __name__ == '__main__':
    print("\n" + "="*60)
    print("FELIX EMPANADAS INVENTORY SYSTEM")
    print("="*60)
    print("\n🌐 Starting web server...\n")
    print("📱 Access from any device on your network:")
    print("   http://192.168.1.XXX:5000  (replace with your desktop IP)")
    print("\n   Or locally: http://localhost:5000\n")
    print("="*60 + "\n")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
