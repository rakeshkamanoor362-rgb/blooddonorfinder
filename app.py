from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify, flash
import json
from datetime import datetime
import hashlib
import os

app = Flask(__name__)
app.secret_key = 'bloodbank_secret_2024'

# ─── In-memory "database" ────────────────────────────────────────────────────
USERS = {
    'admin': {'password': hashlib.md5(b'admin123').hexdigest(), 'role': 'staff', 'name': 'Dr. Admin'},
    'donor1': {'password': hashlib.md5(b'donor123').hexdigest(), 'role': 'donor', 'name': 'Rahul Sharma'},
}

DONORS = [
    {'id':1,'name':'Rahul Sharma','age':28,'gender':'Male','blood_group':'O+','phone':'9876543210','city':'Bengaluru','last_donation':'2026-08-10','units':3,'status':'Active'},
    {'id':2,'name':'Priya Menon','age':25,'gender':'Female','blood_group':'A+','phone':'9876543211','city':'Mumbai','last_donation':'2026-07-15','units':2,'status':'Active'},
    {'id':3,'name':'Arjun Nair','age':32,'gender':'Male','blood_group':'B+','phone':'9876543212','city':'Delhi','last_donation':'2026-09-01','units':5,'status':'Active'},
    {'id':4,'name':'Sunita Rao','age':29,'gender':'Female','blood_group':'AB+','phone':'9876543213','city':'Bengaluru','last_donation':'2026-06-20','units':1,'status':'Active'},
    {'id':5,'name':'Vikram Singh','age':35,'gender':'Male','blood_group':'O-','phone':'9876543214','city':'Chennai','last_donation':'2026-10-05','units':4,'status':'Active'},
    {'id':6,'name':'Sharan kumar boratti','age':35,'gender':'Male','blood_group':'A+','phone':'9876543214','city':'Chennai','last_donation':'2026-04-015','units':4,'status':'Active'},    
]
BLOOD_INVENTORY = {
    'A+': {'units': 45, 'hospitals': ['Apollo Hospital', 'Manipal Hospital', 'Fortis']},
    'A-': {'units': 12, 'hospitals': ['Apollo Hospital', 'St. Philomena']},
    'B+': {'units': 38, 'hospitals': ['Manipal Hospital', 'Narayana Health', 'Victoria Hospital']},
    'B-': {'units': 8,  'hospitals': ['Apollo Hospital', 'Sparsh Hospital']},
    'O+': {'units': 62, 'hospitals': ['Apollo Hospital', 'Manipal Hospital', 'Narayana Health', 'Fortis']},
    'O-': {'units': 15, 'hospitals': ['Apollo Hospital', 'Victoria Hospital', 'NIMHANS']},
    'AB+': {'units': 20, 'hospitals': ['Manipal Hospital', 'Fortis', 'BGS Hospital']},
    'AB-': {'units': 5,  'hospitals': ['Apollo Hospital']},
}

BLOOD_REQUESTS = [
    {'id':1,'patient':'Meena K.','blood_group':'O+','units':2,'hospital':'Apollo','priority':'Emergency','status':'Approved','date':'2024-11-01'},
    {'id':2,'patient':'Suresh P.','blood_group':'A-','units':1,'hospital':'Manipal','priority':'Normal','status':'Pending','date':'2024-11-02'},
    {'id':3,'patient':'Anita B.','blood_group':'B+','units':3,'hospital':'Fortis','priority':'Urgent','status':'Pending','date':'2024-11-03'},
]

next_donor_id = 6
next_request_id = 4

# ─── HTML TEMPLATE ────────────────────────────────────────────────────────────
BASE_HTML = r"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>LifeFlow — Blood Bank & Transfusion Medicine</title>
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=DM+Sans:wght@300;400;500;600&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
:root {
  --crimson: #C8102E;
  --crimson-dark: #9B0A22;
  --crimson-light: #F5E6E8;
  --navy: #0A1F44;
  --navy-mid: #1A3A6E;
  --sky: #E8F0FA;
  --white: #FFFFFF;
  --offwhite: #F9F7F5;
  --gray: #6B7280;
  --gray-light: #E5E7EB;
  --success: #059669;
  --warning: #D97706;
  --danger: #C8102E;
  --shadow: 0 4px 24px rgba(10,31,68,0.10);
  --shadow-lg: 0 12px 48px rgba(10,31,68,0.16);
  --radius: 12px;
  --radius-lg: 20px;
}
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html { scroll-behavior: smooth; }
body { font-family: 'DM Sans', sans-serif; background: var(--offwhite); color: var(--navy); line-height: 1.6; }

/* ── NAV ── */
nav {
  position: fixed; top: 0; left: 0; right: 0; z-index: 1000;
  background: rgba(255,255,255,0.96); backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--gray-light);
  padding: 0 2rem; height: 68px;
  display: flex; align-items: center; justify-content: space-between;
  box-shadow: 0 2px 16px rgba(10,31,68,0.07);
}
.nav-brand { display: flex; align-items: center; gap: 10px; text-decoration: none; }
.nav-brand .logo-icon {
  width: 38px; height: 38px; background: var(--crimson);
  border-radius: 8px; display: flex; align-items: center; justify-content: center;
  color: white; font-size: 18px; font-family: 'Playfair Display', serif; font-weight: 900;
}
.nav-brand span { font-family: 'Playfair Display', serif; font-size: 1.4rem; color: var(--navy); font-weight: 700; }
.nav-brand span em { color: var(--crimson); font-style: normal; }
.nav-links { display: flex; align-items: center; gap: 0.2rem; }
.nav-links a {
  padding: 8px 14px; border-radius: 8px; text-decoration: none;
  color: var(--navy); font-size: 0.9rem; font-weight: 500; transition: all 0.2s;
}
.nav-links a:hover, .nav-links a.active { background: var(--sky); color: var(--crimson); }
.nav-auth { display: flex; gap: 8px; align-items: center; }
.btn { display: inline-flex; align-items: center; gap: 6px; padding: 10px 20px;
  border-radius: 8px; font-size: 0.9rem; font-weight: 600; cursor: pointer;
  border: none; text-decoration: none; transition: all 0.2s; white-space: nowrap; }
.btn-primary { background: var(--crimson); color: white; }
.btn-primary:hover { background: var(--crimson-dark); transform: translateY(-1px); box-shadow: 0 4px 16px rgba(200,16,46,0.3); }
.btn-outline { background: transparent; color: var(--crimson); border: 2px solid var(--crimson); }
.btn-outline:hover { background: var(--crimson); color: white; }
.btn-navy { background: var(--navy); color: white; }
.btn-navy:hover { background: var(--navy-mid); }
.btn-sm { padding: 7px 14px; font-size: 0.82rem; }
.btn-lg { padding: 14px 28px; font-size: 1rem; border-radius: 10px; }
.btn-success { background: var(--success); color: white; }
.btn-warning { background: var(--warning); color: white; }
.hamburger { display: none; flex-direction: column; gap: 5px; cursor: pointer; padding: 4px; }
.hamburger span { width: 24px; height: 2px; background: var(--navy); border-radius: 2px; transition: all 0.3s; }

/* ── MAIN WRAPPER ── */
main { margin-top: 68px; min-height: calc(100vh - 68px); }

/* ── HERO ── */
.hero {
  position: relative; overflow: hidden;
  background: linear-gradient(135deg, var(--navy) 0%, var(--navy-mid) 50%, #1e3a5f 100%);
  padding: 6rem 2rem 5rem; text-align: center; color: white;
}
.hero-bg-pattern {
  position: absolute; inset: 0; opacity: 0.05;
  background-image: radial-gradient(circle at 20% 50%, white 1px, transparent 1px),
    radial-gradient(circle at 80% 20%, white 1px, transparent 1px);
  background-size: 50px 50px;
}
.hero-accent {
  position: absolute; top: -60px; right: -60px;
  width: 300px; height: 300px; border-radius: 50%;
  background: radial-gradient(circle, rgba(200,16,46,0.3), transparent 70%);
}
.hero-accent2 {
  position: absolute; bottom: -80px; left: -40px;
  width: 250px; height: 250px; border-radius: 50%;
  background: radial-gradient(circle, rgba(200,16,46,0.2), transparent 70%);
}
.hero-badge {
  display: inline-flex; align-items: center; gap: 8px;
  background: rgba(200,16,46,0.2); border: 1px solid rgba(200,16,46,0.4);
  color: #fca5a5; padding: 6px 16px; border-radius: 99px; font-size: 0.82rem;
  margin-bottom: 1.5rem; animation: fadeInDown 0.6s ease;
}
.hero h1 {
  font-family: 'Playfair Display', serif; font-size: clamp(2.5rem, 6vw, 4.5rem);
  line-height: 1.15; margin-bottom: 1.2rem; font-weight: 900;
  animation: fadeInUp 0.7s ease;
}
.hero h1 span { color: var(--crimson); }
.hero p {
  font-size: clamp(1rem, 2vw, 1.2rem); color: rgba(255,255,255,0.75);
  max-width: 560px; margin: 0 auto 2.5rem; animation: fadeInUp 0.8s ease;
}
.hero-cta { display: flex; gap: 12px; justify-content: center; flex-wrap: wrap; animation: fadeInUp 0.9s ease; }
.hero-stats {
  display: flex; gap: 2px; justify-content: center; margin-top: 3.5rem;
  flex-wrap: wrap; animation: fadeInUp 1s ease;
}
.hero-stat {
  background: rgba(255,255,255,0.07); backdrop-filter: blur(8px);
  border: 1px solid rgba(255,255,255,0.1);
  padding: 1.2rem 2rem; border-radius: var(--radius);
  min-width: 140px; margin: 4px;
}
.hero-stat .num {
  font-family: 'Playfair Display', serif; font-size: 2rem; font-weight: 900;
  color: var(--crimson); line-height: 1;
}
.hero-stat .lbl { font-size: 0.78rem; color: rgba(255,255,255,0.6); margin-top: 4px; text-transform: uppercase; letter-spacing: 0.05em; }

/* ── EMERGENCY BANNER ── */
.emergency-banner {
  background: linear-gradient(90deg, var(--crimson) 0%, #a30026 100%);
  color: white; padding: 1rem 2rem;
  display: flex; align-items: center; justify-content: center; gap: 1rem;
  flex-wrap: wrap; text-align: center;
}
.emergency-banner .pulse-dot {
  width: 10px; height: 10px; background: white; border-radius: 50%;
  animation: pulse 1.4s infinite;
}
@keyframes pulse { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:0.5;transform:scale(1.4)} }

/* ── SECTIONS ── */
.section { padding: 5rem 2rem; }
.section-alt { background: white; }
.container { max-width: 1140px; margin: 0 auto; }
.section-header { text-align: center; margin-bottom: 3rem; }
.section-header .eyebrow {
  font-size: 0.78rem; font-weight: 600; letter-spacing: 0.12em;
  text-transform: uppercase; color: var(--crimson); margin-bottom: 0.6rem;
}
.section-header h2 {
  font-family: 'Playfair Display', serif; font-size: clamp(1.8rem, 4vw, 2.8rem);
  color: var(--navy); line-height: 1.2;
}
.section-header p { color: var(--gray); margin-top: 0.8rem; font-size: 1.05rem; }

/* ── CARDS ── */
.card {
  background: white; border-radius: var(--radius-lg);
  box-shadow: var(--shadow); border: 1px solid var(--gray-light);
  overflow: hidden; transition: transform 0.25s, box-shadow 0.25s;
}
.card:hover { transform: translateY(-4px); box-shadow: var(--shadow-lg); }
.card-body { padding: 1.8rem; }
.grid { display: grid; gap: 1.5rem; }
.grid-2 { grid-template-columns: repeat(2, 1fr); }
.grid-3 { grid-template-columns: repeat(3, 1fr); }
.grid-4 { grid-template-columns: repeat(4, 1fr); }

/* ── BLOOD GROUP CARDS ── */
.blood-card {
  background: white; border-radius: var(--radius-lg); padding: 1.5rem;
  border: 2px solid var(--gray-light); text-align: center; cursor: pointer;
  transition: all 0.25s;
}
.blood-card:hover, .blood-card.selected { border-color: var(--crimson); background: var(--crimson-light); }
.blood-card .type { font-family: 'Playfair Display', serif; font-size: 2rem; color: var(--crimson); font-weight: 900; }
.blood-card .count { font-size: 0.82rem; color: var(--gray); margin-top: 4px; }
.blood-card .units { font-size: 1.1rem; font-weight: 700; color: var(--navy); margin-top: 2px; }

/* ── FORMS ── */
.form-group { margin-bottom: 1.2rem; }
.form-label { display: block; font-size: 0.85rem; font-weight: 600; color: var(--navy); margin-bottom: 6px; }
.form-control {
  width: 100%; padding: 11px 14px; border: 2px solid var(--gray-light);
  border-radius: 8px; font-size: 0.95rem; font-family: 'DM Sans', sans-serif;
  transition: border-color 0.2s; background: white; color: var(--navy);
}
.form-control:focus { outline: none; border-color: var(--crimson); box-shadow: 0 0 0 3px rgba(200,16,46,0.1); }
.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
.form-select { appearance: none; background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%236B7280' stroke-width='2'%3E%3Cpath d='M6 9l6 6 6-6'/%3E%3C/svg%3E"); background-repeat: no-repeat; background-position: right 12px center; padding-right: 36px; }
.form-card { background: white; border-radius: var(--radius-lg); box-shadow: var(--shadow); padding: 2.5rem; border: 1px solid var(--gray-light); }

/* ── BADGES ── */
.badge { display: inline-block; padding: 3px 10px; border-radius: 99px; font-size: 0.75rem; font-weight: 600; }
.badge-red { background: #FEE2E2; color: #991B1B; }
.badge-green { background: #D1FAE5; color: #065F46; }
.badge-yellow { background: #FEF3C7; color: #92400E; }
.badge-blue { background: #DBEAFE; color: #1E40AF; }

/* ── TABLE ── */
.table-wrapper { overflow-x: auto; border-radius: var(--radius); }
table { width: 100%; border-collapse: collapse; }
th { background: var(--sky); color: var(--navy); font-size: 0.8rem; font-weight: 700;
  text-transform: uppercase; letter-spacing: 0.05em; padding: 12px 16px; text-align: left; }
td { padding: 13px 16px; border-bottom: 1px solid var(--gray-light); font-size: 0.9rem; }
tr:last-child td { border-bottom: none; }
tr:hover td { background: var(--offwhite); }

/* ── STATS ROW ── */
.stats-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 1.2rem; margin-bottom: 2rem; }
.stat-card {
  background: white; border-radius: var(--radius-lg); padding: 1.4rem 1.6rem;
  box-shadow: var(--shadow); border: 1px solid var(--gray-light); display: flex; gap: 1rem; align-items: center;
}
.stat-icon {
  width: 50px; height: 50px; border-radius: 12px;
  display: flex; align-items: center; justify-content: center; font-size: 1.4rem; flex-shrink: 0;
}
.stat-icon.red { background: var(--crimson-light); }
.stat-icon.blue { background: var(--sky); }
.stat-icon.green { background: #D1FAE5; }
.stat-icon.yellow { background: #FEF3C7; }
.stat-num { font-family: 'Playfair Display', serif; font-size: 1.8rem; font-weight: 900; color: var(--navy); line-height: 1; }
.stat-label { font-size: 0.8rem; color: var(--gray); font-weight: 500; margin-top: 3px; }

/* ── TABS ── */
.tabs { display: flex; gap: 4px; background: var(--sky); padding: 5px; border-radius: 10px; width: fit-content; margin-bottom: 1.5rem; }
.tab {
  padding: 8px 18px; border-radius: 7px; font-size: 0.88rem; font-weight: 600;
  cursor: pointer; transition: all 0.2s; border: none; background: transparent; color: var(--gray);
}
.tab.active { background: white; color: var(--crimson); box-shadow: 0 2px 8px rgba(0,0,0,0.08); }

/* ── INFO CARDS ── */
.info-card { background: white; border-radius: var(--radius-lg); padding: 2rem; box-shadow: var(--shadow); border-left: 4px solid var(--crimson); }
.step-card { display: flex; gap: 1.2rem; align-items: flex-start; padding: 1.5rem; background: white; border-radius: var(--radius); box-shadow: var(--shadow); margin-bottom: 1rem; }
.step-num { width: 40px; height: 40px; background: var(--crimson); color: white; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 900; font-size: 1.1rem; flex-shrink: 0; font-family: 'Playfair Display', serif; }

/* ── ALERTS ── */
.alert { padding: 1rem 1.4rem; border-radius: 10px; margin-bottom: 1.2rem; font-size: 0.9rem; display: flex; gap: 10px; align-items: flex-start; }
.alert-success { background: #D1FAE5; color: #065F46; border: 1px solid #6EE7B7; }
.alert-danger { background: #FEE2E2; color: #991B1B; border: 1px solid #FCA5A5; }
.alert-info { background: #DBEAFE; color: #1E40AF; border: 1px solid #93C5FD; }

/* ── FOOTER ── */
footer {
  background: var(--navy); color: rgba(255,255,255,0.7);
  padding: 3rem 2rem 1.5rem;
}
.footer-grid { display: grid; grid-template-columns: 2fr 1fr 1fr 1fr; gap: 2.5rem; max-width: 1140px; margin: 0 auto; }
.footer-brand { margin-bottom: 1rem; }
.footer-brand .logo { font-family: 'Playfair Display', serif; font-size: 1.4rem; color: white; }
.footer-brand .logo em { color: var(--crimson); font-style: normal; }
footer h4 { color: white; font-size: 0.85rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 1rem; }
footer a { color: rgba(255,255,255,0.6); text-decoration: none; font-size: 0.88rem; display: block; margin-bottom: 0.5rem; transition: color 0.2s; }
footer a:hover { color: white; }
.footer-bottom { border-top: 1px solid rgba(255,255,255,0.1); margin-top: 2.5rem; padding-top: 1.2rem; text-align: center; font-size: 0.82rem; max-width: 1140px; margin-left: auto; margin-right: auto; }

/* ── ANIMATIONS ── */
@keyframes fadeInUp { from{opacity:0;transform:translateY(24px)} to{opacity:1;transform:translateY(0)} }
@keyframes fadeInDown { from{opacity:0;transform:translateY(-16px)} to{opacity:1;transform:translateY(0)} }
.fade-in { animation: fadeInUp 0.5s ease forwards; }

/* ── MODAL ── */
.modal-overlay {
  position: fixed; inset: 0; background: rgba(10,31,68,0.6); backdrop-filter: blur(4px);
  z-index: 2000; display: flex; align-items: center; justify-content: center; padding: 1rem;
  opacity: 0; pointer-events: none; transition: opacity 0.25s;
}
.modal-overlay.open { opacity: 1; pointer-events: all; }
.modal-box { background: white; border-radius: var(--radius-lg); padding: 2.5rem; max-width: 460px; width: 100%; box-shadow: var(--shadow-lg); }
.modal-box h3 { font-family: 'Playfair Display', serif; font-size: 1.5rem; color: var(--navy); margin-bottom: 1.5rem; }

/* ── FAQ ── */
.faq-item { border-bottom: 1px solid var(--gray-light); }
.faq-q { padding: 1.1rem 0; display: flex; justify-content: space-between; align-items: center; cursor: pointer; font-weight: 600; color: var(--navy); }
.faq-q:hover { color: var(--crimson); }
.faq-a { padding-bottom: 1rem; color: var(--gray); font-size: 0.92rem; display: none; }
.faq-item.open .faq-a { display: block; }
.faq-item.open .faq-q { color: var(--crimson); }

/* ── CONTACT ── */
.contact-info-card { background: var(--navy); color: white; border-radius: var(--radius-lg); padding: 2rem; }
.contact-info-card h3 { font-family: 'Playfair Display', serif; font-size: 1.4rem; margin-bottom: 1.2rem; }
.contact-item { display: flex; gap: 12px; align-items: flex-start; margin-bottom: 1.2rem; }
.contact-item-icon { width: 36px; height: 36px; background: rgba(200,16,46,0.25); border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 1rem; flex-shrink: 0; }
.emergency-numbers { background: var(--crimson); border-radius: var(--radius); padding: 1.4rem; margin-top: 1.5rem; }
.emergency-numbers h4 { color: white; margin-bottom: 0.8rem; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.08em; }
.emg-num { display: flex; justify-content: space-between; color: white; font-size: 0.9rem; margin-bottom: 0.4rem; }

/* ── INVENTORY BAR ── */
.inv-bar { margin-bottom: 0.8rem; }
.inv-label { display: flex; justify-content: space-between; font-size: 0.85rem; font-weight: 600; color: var(--navy); margin-bottom: 4px; }
.bar-track { background: var(--gray-light); border-radius: 99px; height: 10px; overflow: hidden; }
.bar-fill { height: 100%; border-radius: 99px; transition: width 1.2s cubic-bezier(0.16, 1, 0.3, 1); }
.bar-fill.high { background: linear-gradient(90deg, var(--success), #34D399); }
.bar-fill.mid { background: linear-gradient(90deg, var(--warning), #FBBF24); }
.bar-fill.low { background: linear-gradient(90deg, var(--crimson), #F87171); }

/* ── RESPONSIVE ── */
@media (max-width: 768px) {
  .nav-links { display: none; flex-direction: column; position: fixed; top: 68px; left: 0; right: 0;
    background: white; padding: 1rem; box-shadow: var(--shadow); border-top: 1px solid var(--gray-light); }
  .nav-links.open { display: flex; }
  .hamburger { display: flex; }
  .grid-2, .grid-3, .grid-4 { grid-template-columns: 1fr; }
  .form-row { grid-template-columns: 1fr; }
  .stats-row { grid-template-columns: 1fr 1fr; }
  .footer-grid { grid-template-columns: 1fr 1fr; }
  .hero-stat { min-width: 110px; padding: 1rem 1.2rem; }
  .nav-auth .btn-outline { display: none; }
}
@media (max-width: 480px) {
  .stats-row { grid-template-columns: 1fr; }
  .footer-grid { grid-template-columns: 1fr; }
}

/* ── PAGE SPECIFIC ── */
.page-header {
  background: linear-gradient(135deg, var(--navy), var(--navy-mid));
  color: white; padding: 3.5rem 2rem 3rem; text-align: center;
}
.page-header h1 { font-family: 'Playfair Display', serif; font-size: clamp(1.8rem, 4vw, 2.8rem); margin-bottom: 0.6rem; }
.page-header p { color: rgba(255,255,255,0.7); font-size: 1rem; }
.breadcrumb { font-size: 0.8rem; color: rgba(255,255,255,0.5); margin-bottom: 0.8rem; }
.breadcrumb a { color: rgba(255,255,255,0.6); text-decoration: none; }
.breadcrumb a:hover { color: white; }

.eligibility-item {
  display: flex; gap: 12px; align-items: flex-start; padding: 1rem;
  background: white; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); margin-bottom: 0.8rem;
}
.elig-icon { font-size: 1.2rem; margin-top: 2px; }

.benefit-card { text-align: center; padding: 2rem; }
.benefit-icon { font-size: 2.5rem; margin-bottom: 1rem; display: block; }
.benefit-card h3 { font-family: 'Playfair Display', serif; font-size: 1.1rem; color: var(--navy); margin-bottom: 0.5rem; }
.benefit-card p { font-size: 0.88rem; color: var(--gray); }

/* priority badge */
.priority-emergency { background: #FEE2E2; color: #991B1B; }
.priority-urgent { background: #FEF3C7; color: #92400E; }
.priority-normal { background: #D1FAE5; color: #065F46; }
</style>
</head>
<body>

<!-- NAV -->
<nav>
  <a href="/" class="nav-brand">
    <div class="logo-icon">🩸</div>
    <span>Life<em>Flow</em></span>
  </a>
  <div class="nav-links" id="navLinks">
    <a href="/" class="{{ 'active' if page=='home' }}">Home</a>
    <a href="/availability" class="{{ 'active' if page=='avail' }}">Blood Availability</a>
    <a href="/donate" class="{{ 'active' if page=='donate' }}">Donate</a>
    <a href="/request" class="{{ 'active' if page=='request' }}">Request Blood</a>
    <a href="/info" class="{{ 'active' if page=='info' }}">Info</a>
    {% if session.get('user') %}
    <a href="/dashboard" class="{{ 'active' if page=='dash' }}">Dashboard</a>
    {% endif %}
    <a href="/contact" class="{{ 'active' if page=='contact' }}">Contact</a>
  </div>
  <div class="nav-auth">
    {% if session.get('user') %}
      <span style="font-size:0.85rem;color:var(--gray);margin-right:4px;">{{ session['name'] }}</span>
      <a href="/logout" class="btn btn-outline btn-sm">Logout</a>
    {% else %}
      <a href="/login" class="btn btn-outline btn-sm">Login</a>
      <a href="/signup" class="btn btn-primary btn-sm">Sign Up</a>
    {% endif %}
  </div>
  <div class="hamburger" onclick="toggleNav()">
    <span></span><span></span><span></span>
  </div>
</nav>

<main>
{% with messages = get_flashed_messages(with_categories=true) %}
  {% if messages %}
    <div style="position:fixed;top:80px;right:1.5rem;z-index:1500;max-width:360px;">
    {% for cat, msg in messages %}
      <div class="alert alert-{{ 'success' if cat=='success' else 'danger' }}" style="animation:fadeInDown 0.4s ease;margin-bottom:8px;">
        {{ '✓' if cat=='success' else '⚠' }} {{ msg }}
      </div>
    {% endfor %}
    </div>
  {% endif %}
{% endwith %}

{{ content }}
</main>

<!-- FOOTER -->
<footer>
  <div class="footer-grid">
    <div>
      <div class="footer-brand">
        <div class="logo">Life<em>Flow</em></div>
      </div>
      <p style="font-size:0.88rem;line-height:1.7;margin-top:0.5rem;">Connecting donors to patients, saving lives every day through safe and efficient blood transfusion services.</p>
      <div style="margin-top:1rem;display:flex;gap:8px;">
        <a href="#" style="display:inline-flex;width:34px;height:34px;background:rgba(255,255,255,0.1);border-radius:8px;align-items:center;justify-content:center;">📘</a>
        <a href="#" style="display:inline-flex;width:34px;height:34px;background:rgba(255,255,255,0.1);border-radius:8px;align-items:center;justify-content:center;">🐦</a>
        <a href="#" style="display:inline-flex;width:34px;height:34px;background:rgba(255,255,255,0.1);border-radius:8px;align-items:center;justify-content:center;">📸</a>
      </div>
    </div>
    <div>
      <h4>Quick Links</h4>
      <a href="/availability">Blood Availability</a>
      <a href="/donate">Donate Blood</a>
      <a href="/request">Request Blood</a>
      <a href="/info">Donation Info</a>
    </div>
    <div>
      <h4>Services</h4>
      <a href="#">Blood Typing</a>
      <a href="#">Plasma Donation</a>
      <a href="#">Platelet Donation</a>
      <a href="#">Mobile Camps</a>
    </div>
    <div>
      <h4>Emergency</h4>
      <a href="tel:+911234567890">☎ +91 123 456 7890</a>
      <a href="tel:104">🚨 National: 104</a>
      <a href="/contact">📍 Find Us</a>
      <a href="#">24/7 Helpline</a>
    </div>
  </div>
  <div class="footer-bottom">
    <p>© 2024 LifeFlow Blood Bank & Transfusion Medicine. All rights reserved. | Saving lives, one unit at a time. 🩸</p>
  </div>
</footer>

<!-- LOGIN MODAL -->
<div class="modal-overlay" id="loginModal">
  <div class="modal-box">
    <h3>🩸 Welcome Back</h3>
    <form method="POST" action="/login">
      <div class="form-group">
        <label class="form-label">Username</label>
        <input type="text" name="username" class="form-control" placeholder="Enter username" required>
      </div>
      <div class="form-group">
        <label class="form-label">Password</label>
        <input type="password" name="password" class="form-control" placeholder="Enter password" required>
      </div>
      <button type="submit" class="btn btn-primary" style="width:100%">Login</button>
    </form>
    <p style="text-align:center;margin-top:1rem;font-size:0.85rem;color:var(--gray);">
      Don't have an account? <a href="/signup" style="color:var(--crimson);">Sign up</a>
    </p>
    <button onclick="document.getElementById('loginModal').classList.remove('open')" style="position:absolute;top:1rem;right:1rem;background:none;border:none;font-size:1.2rem;cursor:pointer;color:var(--gray)">✕</button>
  </div>
</div>

<script>
function toggleNav() {
  document.getElementById('navLinks').classList.toggle('open');
}

// FAQ toggle
document.querySelectorAll('.faq-q').forEach(q => {
  q.addEventListener('click', () => {
    const item = q.closest('.faq-item');
    item.classList.toggle('open');
  });
});

// Auto-dismiss flash messages
setTimeout(() => {
  document.querySelectorAll('.alert').forEach(a => {
    a.style.transition = 'opacity 0.5s';
    a.style.opacity = '0';
    setTimeout(() => a.remove(), 500);
  });
}, 4000);

// Animate inventory bars
function animateBars() {
  document.querySelectorAll('.bar-fill').forEach(bar => {
    const w = bar.getAttribute('data-width');
    bar.style.width = w + '%';
  });
}
setTimeout(animateBars, 300);
</script>
</body>
</html>
"""

# ─── HOME PAGE ───────────────────────────────────────────────────────────────
HOME_CONTENT = """
<div class="hero">
  <div class="hero-bg-pattern"></div>
  <div class="hero-accent"></div>
  <div class="hero-accent2"></div>
  <div style="position:relative;z-index:1;max-width:800px;margin:0 auto">
    <div class="hero-badge">
      🩸 India's Trusted Blood Management Network
    </div>
    <h1>Donate Blood,<br><span>Save Lives</span></h1>
    <p>Every drop counts. Connect with 200+ hospitals across India. Safe, fast, and life-saving blood management at your fingertips.</p>
    <div class="hero-cta">
      <a href="/donate" class="btn btn-primary btn-lg">🩸 Donate Now</a>
      <a href="/availability" class="btn btn-lg" style="background:rgba(255,255,255,0.15);color:white;border:2px solid rgba(255,255,255,0.3);backdrop-filter:blur(8px);">🔍 Find Blood</a>
      <a href="/signup" class="btn btn-lg" style="background:white;color:var(--crimson);">📝 Register</a>
    </div>
    <div class="hero-stats">
      <div class="hero-stat"><div class="num">12,480</div><div class="lbl">Registered Donors</div></div>
      <div class="hero-stat"><div class="num">3,847</div><div class="lbl">Units Available</div></div>
      <div class="hero-stat"><div class="num">214</div><div class="lbl">Partner Hospitals</div></div>
      <div class="hero-stat"><div class="num">98.6%</div><div class="lbl">Success Rate</div></div>
    </div>
  </div>
</div>

<!-- Emergency Banner -->
<div class="emergency-banner">
  <div class="pulse-dot"></div>
  <strong>🚨 EMERGENCY ALERT:</strong>
  <span>O- blood critically needed at Apollo Bengaluru — call <strong>+91 98765 43210</strong> immediately</span>
  <a href="/request" class="btn btn-sm" style="background:white;color:var(--crimson);margin-left:8px;">Request Now</a>
</div>

<!-- Blood Availability Quick View -->
<section class="section section-alt">
  <div class="container">
    <div class="section-header">
      <div class="eyebrow">Real-Time Data</div>
      <h2>Blood Stock Overview</h2>
      <p>Live inventory across all partner blood banks</p>
    </div>
    <div class="grid grid-4">
      {% for group, data in blood_inventory.items() %}
      <a href="/availability?group={{ group }}" style="text-decoration:none">
        <div class="blood-card">
          <div class="type">{{ group }}</div>
          <div class="units" style="font-size:1.4rem;margin-top:4px;color:{{ 'var(--success)' if data.units > 30 else ('var(--warning)' if data.units > 10 else 'var(--crimson)') }}">{{ data.units }}</div>
          <div class="count">units available</div>
          <div style="margin-top:8px;">
            <span class="badge {{ 'badge-green' if data.units > 30 else ('badge-yellow' if data.units > 10 else 'badge-red') }}">
              {{ 'Sufficient' if data.units > 30 else ('Low' if data.units > 10 else 'Critical') }}
            </span>
          </div>
        </div>
      </a>
      {% endfor %}
    </div>
  </div>
</section>

<!-- How It Works -->
<section class="section">
  <div class="container">
    <div class="section-header">
      <div class="eyebrow">Simple Process</div>
      <h2>How LifeFlow Works</h2>
      <p>Three simple steps to donate or receive blood</p>
    </div>
    <div class="grid grid-3">
      <div class="card"><div class="card-body" style="text-align:center">
        <div style="width:64px;height:64px;background:var(--crimson-light);border-radius:50%;display:flex;align-items:center;justify-content:center;margin:0 auto 1rem;font-size:1.8rem">📝</div>
        <h3 style="font-family:'Playfair Display',serif;font-size:1.2rem;color:var(--navy);margin-bottom:0.6rem">1. Register</h3>
        <p style="font-size:0.88rem;color:var(--gray)">Create your donor profile with blood group and health information. Quick 2-minute setup.</p>
      </div></div>
      <div class="card"><div class="card-body" style="text-align:center">
        <div style="width:64px;height:64px;background:var(--sky);border-radius:50%;display:flex;align-items:center;justify-content:center;margin:0 auto 1rem;font-size:1.8rem">🏥</div>
        <h3 style="font-family:'Playfair Display',serif;font-size:1.2rem;color:var(--navy);margin-bottom:0.6rem">2. Schedule</h3>
        <p style="font-size:0.88rem;color:var(--gray)">Book a convenient donation slot at any partner hospital or blood bank near you.</p>
      </div></div>
      <div class="card"><div class="card-body" style="text-align:center">
        <div style="width:64px;height:64px;background:#D1FAE5;border-radius:50%;display:flex;align-items:center;justify-content:center;margin:0 auto 1rem;font-size:1.8rem">🩸</div>
        <h3 style="font-family:'Playfair Display',serif;font-size:1.2rem;color:var(--navy);margin-bottom:0.6rem">3. Donate & Save</h3>
        <p style="font-size:0.88rem;color:var(--gray)">Complete your donation and receive a digital certificate. Track your impact over time.</p>
      </div></div>
    </div>
  </div>
</section>

<!-- Recent Donors -->
<section class="section section-alt">
  <div class="container">
    <div class="section-header">
      <div class="eyebrow">Our Heroes</div>
      <h2>Recent Donors</h2>
    </div>
    <div class="table-wrapper card">
      <table>
        <thead><tr><th>Name</th><th>Blood Group</th><th>City</th><th>Donations</th><th>Last Donated</th><th>Status</th></tr></thead>
        <tbody>
        {% for d in donors[:5] %}
        <tr>
          <td><strong>{{ d.name }}</strong></td>
          <td><span style="font-family:'Playfair Display',serif;font-size:1.1rem;font-weight:900;color:var(--crimson)">{{ d.blood_group }}</span></td>
          <td>{{ d.city }}</td>
          <td>{{ d.units }} units</td>
          <td>{{ d.last_donation }}</td>
          <td><span class="badge badge-green">{{ d.status }}</span></td>
        </tr>
        {% endfor %}
        </tbody>
      </table>
    </div>
    <div style="text-align:center;margin-top:1.5rem">
      <a href="/donate" class="btn btn-primary">Become a Donor →</a>
    </div>
  </div>
</section>
"""

# ─── AVAILABILITY PAGE ────────────────────────────────────────────────────────
AVAIL_CONTENT = """
<div class="page-header">
  <div class="breadcrumb"><a href="/">Home</a> / Blood Availability</div>
  <h1>🔍 Blood Availability</h1>
  <p>Real-time blood stock across all partner hospitals</p>
</div>

<section class="section">
  <div class="container">
    <!-- Search/Filter Bar -->
    <div class="form-card" style="margin-bottom:2rem">
      <form method="GET" action="/availability">
        <div class="form-row" style="align-items:flex-end">
          <div class="form-group" style="margin-bottom:0">
            <label class="form-label">Blood Group</label>
            <select name="group" class="form-control form-select">
              <option value="">All Blood Groups</option>
              {% for g in ['A+','A-','B+','B-','O+','O-','AB+','AB-'] %}
              <option value="{{ g }}" {{ 'selected' if selected_group==g }}>{{ g }}</option>
              {% endfor %}
            </select>
          </div>
          <div class="form-group" style="margin-bottom:0">
            <label class="form-label">City</label>
            <select name="city" class="form-control form-select">
              <option value="">All Cities</option>
              {% for c in ['Bengaluru','Mumbai','Delhi','Chennai','Hyderabad'] %}
              <option value="{{ c }}" {{ 'selected' if selected_city==c }}>{{ c }}</option>
              {% endfor %}
            </select>
          </div>
          <div>
            <button type="submit" class="btn btn-primary">Search</button>
            <a href="/availability" class="btn btn-outline" style="margin-left:8px">Clear</a>
          </div>
        </div>
      </form>
    </div>

    <!-- Blood Group Cards Grid -->
    <div class="grid grid-4" style="margin-bottom:2.5rem">
      {% for group, data in blood_inventory.items() %}
      {% if not selected_group or selected_group == group %}
      <div class="card" style="border-top:4px solid {{ 'var(--success)' if data.units > 30 else ('var(--warning)' if data.units > 10 else 'var(--crimson)') }}">
        <div class="card-body">
          <div style="display:flex;justify-content:space-between;align-items:flex-start">
            <div>
              <div style="font-family:'Playfair Display',serif;font-size:2.5rem;font-weight:900;color:var(--crimson);line-height:1">{{ group }}</div>
              <div style="font-size:0.78rem;color:var(--gray);text-transform:uppercase;letter-spacing:0.05em;margin-top:2px">Blood Type</div>
            </div>
            <div style="text-align:right">
              <div style="font-size:2rem;font-weight:900;color:var(--navy)">{{ data.units }}</div>
              <div style="font-size:0.78rem;color:var(--gray)">units</div>
            </div>
          </div>
          <div style="margin:1rem 0">
            <div class="bar-track">
              <div class="bar-fill {{ 'high' if data.units > 30 else ('mid' if data.units > 10 else 'low') }}"
                   data-width="{{ [data.units * 1.5, 100]|min }}" style="width:0%"></div>
            </div>
          </div>
          <div>
            {% for h in data.hospitals[:2] %}
            <div style="font-size:0.78rem;color:var(--gray);padding:3px 0;display:flex;align-items:center;gap:5px">
              <span style="color:var(--success)">●</span> {{ h }}
            </div>
            {% endfor %}
            {% if data.hospitals|length > 2 %}<div style="font-size:0.75rem;color:var(--crimson);margin-top:3px">+{{ data.hospitals|length - 2 }} more hospitals</div>{% endif %}
          </div>
          <a href="/request?group={{ group }}" class="btn btn-primary btn-sm" style="width:100%;justify-content:center;margin-top:1rem">Request This Group</a>
        </div>
      </div>
      {% endif %}
      {% endfor %}
    </div>

    <!-- Inventory Table -->
    <div class="card">
      <div class="card-body" style="padding-bottom:0">
        <h3 style="font-family:'Playfair Display',serif;font-size:1.3rem;color:var(--navy);margin-bottom:1.2rem">Full Inventory Details</h3>
      </div>
      <div class="table-wrapper">
        <table>
          <thead><tr><th>Blood Type</th><th>Units Available</th><th>Status</th><th>Available At</th><th>Action</th></tr></thead>
          <tbody>
          {% for group, data in blood_inventory.items() %}
          {% if not selected_group or selected_group == group %}
          <tr>
            <td><strong style="font-family:'Playfair Display',serif;font-size:1.2rem;color:var(--crimson)">{{ group }}</strong></td>
            <td><strong>{{ data.units }}</strong> units</td>
            <td>
              <span class="badge {{ 'badge-green' if data.units > 30 else ('badge-yellow' if data.units > 10 else 'badge-red') }}">
                {{ 'Sufficient' if data.units > 30 else ('Low' if data.units > 10 else 'Critical') }}
              </span>
            </td>
            <td>{{ data.hospitals|join(', ') }}</td>
            <td><a href="/request?group={{ group }}" class="btn btn-primary btn-sm">Request</a></td>
          </tr>
          {% endif %}
          {% endfor %}
          </tbody>
        </table>
      </div>
    </div>
  </div>
</section>
"""

# ─── DONOR REGISTRATION ───────────────────────────────────────────────────────
DONATE_CONTENT = """
<div class="page-header">
  <div class="breadcrumb"><a href="/">Home</a> / Donor Registration</div>
  <h1>🩸 Become a Donor</h1>
  <p>Register today and start saving lives</p>
</div>

<section class="section">
  <div class="container">
    <div style="display:grid;grid-template-columns:1fr 360px;gap:2rem;align-items:start" class="donate-grid">
      <div class="form-card">
        <h2 style="font-family:'Playfair Display',serif;font-size:1.6rem;color:var(--navy);margin-bottom:0.5rem">Donor Registration Form</h2>
        <p style="color:var(--gray);font-size:0.9rem;margin-bottom:1.8rem">Fill in your details to join our life-saving network</p>
        <form method="POST" action="/donate">
          <div class="form-row">
            <div class="form-group">
              <label class="form-label">Full Name *</label>
              <input type="text" name="name" class="form-control" placeholder="Your full name" required>
            </div>
            <div class="form-group">
              <label class="form-label">Age *</label>
              <input type="number" name="age" class="form-control" placeholder="18-65" min="18" max="65" required>
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label class="form-label">Gender *</label>
              <select name="gender" class="form-control form-select" required>
                <option value="">Select gender</option>
                <option>Male</option><option>Female</option><option>Other</option>
              </select>
            </div>
            <div class="form-group">
              <label class="form-label">Blood Group *</label>
              <select name="blood_group" class="form-control form-select" required>
                <option value="">Select blood group</option>
                {% for g in ['A+','A-','B+','B-','O+','O-','AB+','AB-'] %}
                <option value="{{ g }}">{{ g }}</option>
                {% endfor %}
              </select>
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label class="form-label">Phone Number *</label>
              <input type="tel" name="phone" class="form-control" placeholder="10-digit mobile" required>
            </div>
            <div class="form-group">
              <label class="form-label">City *</label>
              <select name="city" class="form-control form-select" required>
                <option value="">Select city</option>
                {% for c in ['Bengaluru','Mumbai','Delhi','Chennai','Hyderabad','Kolkata','Pune'] %}
                <option>{{ c }}</option>
                {% endfor %}
              </select>
            </div>
          </div>
          <div class="form-group">
            <label class="form-label">Address</label>
            <textarea name="address" class="form-control" rows="2" placeholder="Street address, area"></textarea>
          </div>
          <div class="form-group">
            <label class="form-label">Last Donation Date (if applicable)</label>
            <input type="date" name="last_donation" class="form-control">
          </div>
          <div class="form-group" style="margin-top:1.2rem">
            <label style="display:flex;gap:10px;align-items:flex-start;cursor:pointer;font-size:0.87rem;color:var(--gray)">
              <input type="checkbox" required style="margin-top:3px;accent-color:var(--crimson)">
              I confirm I am in good health, between 18-65 years old, and weigh at least 50 kg. I agree to the terms and conditions.
            </label>
          </div>
          <button type="submit" class="btn btn-primary btn-lg" style="width:100%;justify-content:center;margin-top:0.5rem">
            🩸 Register as Donor
          </button>
        </form>
      </div>

      <div>
        <div class="info-card" style="margin-bottom:1.2rem">
          <h4 style="color:var(--navy);font-weight:700;margin-bottom:0.8rem">✅ Eligibility Checklist</h4>
          {% for item in ['Age 18–65 years','Weight ≥ 50 kg','Hemoglobin ≥ 12.5 g/dL','No major illness','90 days since last donation','No recent surgery'] %}
          <div style="display:flex;gap:8px;align-items:center;font-size:0.85rem;color:var(--gray);margin-bottom:6px">
            <span style="color:var(--success);font-size:1rem">✓</span> {{ item }}
          </div>
          {% endfor %}
        </div>
        <div class="card"><div class="card-body">
          <h4 style="color:var(--navy);font-weight:700;margin-bottom:0.8rem">📊 Your Impact</h4>
          <div style="text-align:center;padding:1rem 0">
            <div style="font-family:'Playfair Display',serif;font-size:3rem;color:var(--crimson);font-weight:900">3</div>
            <div style="font-size:0.85rem;color:var(--gray)">lives saved per donation</div>
          </div>
          <div style="border-top:1px solid var(--gray-light);padding-top:1rem;font-size:0.83rem;color:var(--gray)">
            Every unit of blood can be separated into red cells, plasma, and platelets — each helping a different patient.
          </div>
        </div></div>
        <div class="card" style="margin-top:1.2rem;background:var(--crimson);color:white;border:none"><div class="card-body">
          <h4 style="color:white;margin-bottom:0.5rem">🚨 Urgent Need</h4>
          <p style="font-size:0.85rem;opacity:0.85">O- and AB- blood groups critically needed. If you have these groups, please donate today!</p>
          <a href="/contact" class="btn btn-sm" style="background:white;color:var(--crimson);margin-top:0.8rem">Call Helpline</a>
        </div></div>
      </div>
    </div>
  </div>
</section>
<style>
@media(max-width:768px){.donate-grid{grid-template-columns:1fr!important}}
</style>
"""

# ─── BLOOD REQUEST PAGE ───────────────────────────────────────────────────────
REQUEST_CONTENT = """
<div class="page-header">
  <div class="breadcrumb"><a href="/">Home</a> / Request Blood</div>
  <h1>🏥 Request Blood</h1>
  <p>Submit an emergency or planned blood request</p>
</div>

<section class="section">
  <div class="container">
    <div style="display:grid;grid-template-columns:1fr 320px;gap:2rem;align-items:start" class="req-grid">
      <div class="form-card">
        <h2 style="font-family:'Playfair Display',serif;font-size:1.6rem;color:var(--navy);margin-bottom:1.8rem">Blood Request Form</h2>
        <form method="POST" action="/request">
          <div class="form-row">
            <div class="form-group">
              <label class="form-label">Patient Name *</label>
              <input type="text" name="patient" class="form-control" placeholder="Full patient name" required>
            </div>
            <div class="form-group">
              <label class="form-label">Hospital *</label>
              <select name="hospital" class="form-control form-select" required>
                <option value="">Select hospital</option>
                {% for h in ['Apollo Hospital','Manipal Hospital','Fortis','Narayana Health','Victoria Hospital','St. Philomena','NIMHANS'] %}
                <option>{{ h }}</option>
                {% endfor %}
              </select>
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label class="form-label">Required Blood Group *</label>
              <select name="blood_group" class="form-control form-select" required>
                <option value="">Select blood group</option>
                {% for g in ['A+','A-','B+','B-','O+','O-','AB+','AB-'] %}
                <option value="{{ g }}" {{ 'selected' if preselect_group==g }}>{{ g }}</option>
                {% endfor %}
              </select>
            </div>
            <div class="form-group">
              <label class="form-label">Units Required *</label>
              <input type="number" name="units" class="form-control" placeholder="e.g. 2" min="1" max="20" required>
            </div>
          </div>
          <div class="form-group">
            <label class="form-label">Contact Number *</label>
            <input type="tel" name="contact" class="form-control" placeholder="Emergency contact" required>
          </div>
          <div class="form-group">
            <label class="form-label">Priority Level *</label>
            <div style="display:flex;gap:10px;flex-wrap:wrap;margin-top:6px">
              {% for p, color, desc in [('Normal','#059669','Scheduled procedure, within 48h'),('Urgent','#D97706','Within 12 hours needed'),('Emergency','#C8102E','Immediate, life-threatening')] %}
              <label style="display:flex;align-items:center;gap:8px;cursor:pointer;padding:10px 16px;border:2px solid var(--gray-light);border-radius:8px;flex:1;min-width:140px;transition:all 0.2s">
                <input type="radio" name="priority" value="{{ p }}" style="accent-color:{{ color }}">
                <div>
                  <div style="font-size:0.85rem;font-weight:700;color:var(--navy)">{{ p }}</div>
                  <div style="font-size:0.72rem;color:var(--gray)">{{ desc }}</div>
                </div>
              </label>
              {% endfor %}
            </div>
          </div>
          <div class="form-group">
            <label class="form-label">Additional Notes</label>
            <textarea name="notes" class="form-control" rows="2" placeholder="Any special requirements or medical details..."></textarea>
          </div>
          <button type="submit" class="btn btn-primary btn-lg" style="width:100%;justify-content:center">
            📋 Submit Request
          </button>
        </form>
      </div>

      <div>
        <div class="contact-info-card" style="margin-bottom:1.2rem">
          <h3>🚨 Emergency Line</h3>
          <div style="font-size:1.8rem;font-weight:900;color:white;margin-bottom:0.3rem">1800-XXX-XXXX</div>
          <div style="font-size:0.85rem;opacity:0.7">Available 24/7 for emergencies</div>
          <div style="background:rgba(255,255,255,0.1);border-radius:8px;padding:12px;margin-top:1rem;font-size:0.85rem">
            For life-threatening emergencies, call immediately — do not wait for form approval.
          </div>
        </div>

        <div class="card"><div class="card-body">
          <h4 style="color:var(--navy);font-weight:700;margin-bottom:1rem">📋 Recent Requests</h4>
          {% for r in requests[-3:]|reverse %}
          <div style="border-bottom:1px solid var(--gray-light);padding:10px 0;last:border-none">
            <div style="display:flex;justify-content:space-between;align-items:center">
              <span style="font-weight:600;font-size:0.88rem">{{ r.patient }}</span>
              <span class="badge badge-{{ 'red' if r.priority=='Emergency' else ('yellow' if r.priority=='Urgent' else 'green') }}">{{ r.priority }}</span>
            </div>
            <div style="font-size:0.78rem;color:var(--gray);margin-top:3px">{{ r.blood_group }} · {{ r.units }} units · {{ r.hospital }}</div>
            <div style="font-size:0.78rem;margin-top:2px"><span class="badge {{ 'badge-green' if r.status=='Approved' else 'badge-yellow' }}">{{ r.status }}</span></div>
          </div>
          {% endfor %}
        </div></div>
      </div>
    </div>
  </div>
</section>
<style>@media(max-width:768px){.req-grid{grid-template-columns:1fr!important}}</style>
"""

# ─── INFO PAGE ────────────────────────────────────────────────────────────────
INFO_CONTENT = """
<div class="page-header">
  <div class="breadcrumb"><a href="/">Home</a> / Donation Information</div>
  <h1>📚 Blood Donation Info</h1>
  <p>Everything you need to know about donating blood</p>
</div>

<section class="section section-alt">
  <div class="container">
    <div class="tabs" id="infoTabs">
      <button class="tab active" onclick="showTab('eligibility',this)">Eligibility</button>
      <button class="tab" onclick="showTab('process',this)">Process</button>
      <button class="tab" onclick="showTab('benefits',this)">Benefits</button>
      <button class="tab" onclick="showTab('faq',this)">FAQs</button>
    </div>

    <!-- Eligibility -->
    <div id="eligibility" class="tab-panel">
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:1.2rem" class="info-two-col">
        <div>
          <h3 style="font-family:'Playfair Display',serif;font-size:1.4rem;color:var(--navy);margin-bottom:1rem">✅ Who Can Donate</h3>
          {% for item in ['Age between 18 and 65 years','Body weight ≥ 50 kg','Hemoglobin ≥ 12.5 g/dL (women), ≥ 13.0 (men)','Good general health on day of donation','No fever, cold or infection','Blood pressure within normal range','At least 90 days since last whole blood donation','No tattoo or piercing in last 6 months'] %}
          <div class="eligibility-item">
            <span class="elig-icon">✅</span>
            <div style="font-size:0.9rem;color:var(--navy)">{{ item }}</div>
          </div>
          {% endfor %}
        </div>
        <div>
          <h3 style="font-family:'Playfair Display',serif;font-size:1.4rem;color:var(--crimson);margin-bottom:1rem">❌ Who Cannot Donate</h3>
          {% for item in ['Pregnant or breastfeeding women','Currently on antibiotics','HIV, Hepatitis B/C positive','Recent major surgery (within 6 months)','History of heart disease or cancer','Severe diabetes or hypertension','Under influence of alcohol','Certain medications (ask your doctor)'] %}
          <div class="eligibility-item" style="border-left:3px solid var(--crimson)">
            <span class="elig-icon">❌</span>
            <div style="font-size:0.9rem;color:var(--navy)">{{ item }}</div>
          </div>
          {% endfor %}
        </div>
      </div>
    </div>

    <!-- Process -->
    <div id="process" class="tab-panel" style="display:none">
      <h3 style="font-family:'Playfair Display',serif;font-size:1.4rem;color:var(--navy);margin-bottom:1.5rem">Donation Process — Step by Step</h3>
      {% for step in [('Registration','Fill out the donor registration form and provide photo ID. This takes about 5 minutes.'),('Medical Screening','A quick health check: hemoglobin, blood pressure, temperature, and pulse. Done by trained staff.'),('Blood Donation','The actual donation takes only 8–10 minutes. A sterile needle is used; you donate 350–450 ml.'),('Rest & Refreshment','Relax for 10–15 minutes. Enjoy juice and biscuits. Hydrate well.'),('Certificate & Tracking','Receive your digital donation certificate and track your donations through the app.')] %}
      <div class="step-card">
        <div class="step-num">{{ loop.index }}</div>
        <div>
          <h4 style="color:var(--navy);font-weight:700;margin-bottom:0.3rem">{{ step[0] }}</h4>
          <p style="font-size:0.88rem;color:var(--gray)">{{ step[1] }}</p>
        </div>
      </div>
      {% endfor %}
      <div class="alert alert-info" style="margin-top:1.5rem">
        💡 <strong>Tip:</strong> Drink extra fluids and eat a healthy meal before donating. Avoid fatty foods 4 hours before donation.
      </div>
    </div>

    <!-- Benefits -->
    <div id="benefits" class="tab-panel" style="display:none">
      <h3 style="font-family:'Playfair Display',serif;font-size:1.4rem;color:var(--navy);margin-bottom:1.5rem">Why Donate Blood?</h3>
      <div class="grid grid-3">
        {% for benefit in [('❤️','Save Lives','One donation can save up to 3 lives. Blood is needed every 2 seconds across the world.'),('🏥','Free Health Check','Get a mini health screening — hemoglobin, blood pressure, pulse — absolutely free.'),('🔬','Detect Diseases','Blood tests can reveal undetected conditions like anemia or blood disorders early.'),('💪','Reduce Risk','Regular donation reduces harmful iron stores, lowering risk of heart disease.'),('🧠','Mental Wellbeing','The act of giving creates a sense of purpose and community belonging.'),('🎖️','Social Recognition','Receive certificates, badges, and public recognition for your life-saving contribution.')] %}
        <div class="card benefit-card">
          <span class="benefit-icon">{{ benefit[0] }}</span>
          <h3>{{ benefit[1] }}</h3>
          <p>{{ benefit[2] }}</p>
        </div>
        {% endfor %}
      </div>
    </div>

    <!-- FAQ -->
    <div id="faq" class="tab-panel" style="display:none">
      <h3 style="font-family:'Playfair Display',serif;font-size:1.4rem;color:var(--navy);margin-bottom:1.5rem">Frequently Asked Questions</h3>
      <div style="max-width:700px">
        {% for q, a in [('Does blood donation hurt?','Most donors report only a brief pinch when the needle is inserted. The actual donation is painless. Trained nurses ensure maximum comfort.'),('How long does a donation take?','The full process (registration to recovery) takes 45–60 minutes. The actual blood draw is only 8–10 minutes.'),('How often can I donate?','Whole blood: every 90 days (3 months). Platelets: every 2 weeks. Plasma: every 4 weeks.'),('Will I feel weak after donating?','Most people feel perfectly fine. Your body replaces the fluid in 24 hours and red cells within a few weeks. Eat and drink well after.'),('Is donated blood tested for diseases?','Yes. All donated blood is rigorously tested for HIV, Hepatitis B & C, syphilis, and malaria before use.'),('Can I donate if I have diabetes?','Donors with well-controlled diabetes on oral medication (not insulin) may be eligible. Consult our medical team.'),('What is the rarest blood group?','AB- is the rarest (less than 1% of population). O- is the universal donor and always in high demand.')] %}
        <div class="faq-item">
          <div class="faq-q">{{ q }} <span>▾</span></div>
          <div class="faq-a">{{ a }}</div>
        </div>
        {% endfor %}
      </div>
    </div>
  </div>
</section>

<script>
function showTab(id, el) {
  document.querySelectorAll('.tab-panel').forEach(p => p.style.display = 'none');
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.getElementById(id).style.display = 'block';
  el.classList.add('active');
}
</script>
<style>@media(max-width:768px){.info-two-col{grid-template-columns:1fr!important}}</style>
"""

# ─── DASHBOARD PAGE ───────────────────────────────────────────────────────────
DASHBOARD_CONTENT = """
<div class="page-header">
  <div class="breadcrumb"><a href="/">Home</a> / Dashboard</div>
  <h1>📊 Staff Dashboard</h1>
  <p>Blood bank inventory and management overview</p>
</div>

<section class="section">
  <div class="container">
    <div class="stats-row">
      <div class="stat-card">
        <div class="stat-icon red">🩸</div>
        <div><div class="stat-num">{{ total_units }}</div><div class="stat-label">Total Blood Units</div></div>
      </div>
      <div class="stat-card">
        <div class="stat-icon blue">👥</div>
        <div><div class="stat-num">{{ donor_count }}</div><div class="stat-label">Registered Donors</div></div>
      </div>
      <div class="stat-card">
        <div class="stat-icon yellow">📋</div>
        <div><div class="stat-num">{{ pending_count }}</div><div class="stat-label">Pending Requests</div></div>
      </div>
      <div class="stat-card">
        <div class="stat-icon green">✅</div>
        <div><div class="stat-num">{{ approved_count }}</div><div class="stat-label">Requests Approved</div></div>
      </div>
    </div>

    <div style="display:grid;grid-template-columns:1fr 1fr;gap:1.5rem;margin-bottom:1.5rem" class="chart-grid">
      <!-- Blood Stock Chart -->
      <div class="card"><div class="card-body">
        <h3 style="font-family:'Playfair Display',serif;font-size:1.2rem;color:var(--navy);margin-bottom:1rem">Blood Group Inventory</h3>
        <canvas id="stockChart" height="220"></canvas>
      </div></div>
      <!-- Inventory Bars -->
      <div class="card"><div class="card-body">
        <h3 style="font-family:'Playfair Display',serif;font-size:1.2rem;color:var(--navy);margin-bottom:1.2rem">Stock Levels</h3>
        {% for group, data in blood_inventory.items() %}
        <div class="inv-bar">
          <div class="inv-label"><span>{{ group }}</span><span>{{ data.units }} units</span></div>
          <div class="bar-track"><div class="bar-fill {{ 'high' if data.units > 30 else ('mid' if data.units > 10 else 'low') }}" data-width="{{ [data.units * 1.5, 100]|min }}" style="width:0%"></div></div>
        </div>
        {% endfor %}
      </div></div>
    </div>

    <!-- Requests Table -->
    <div class="card" style="margin-bottom:1.5rem">
      <div class="card-body" style="padding-bottom:0">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:1rem">
          <h3 style="font-family:'Playfair Display',serif;font-size:1.2rem;color:var(--navy)">Blood Requests</h3>
          <a href="/request" class="btn btn-primary btn-sm">+ New Request</a>
        </div>
      </div>
      <div class="table-wrapper">
        <table>
          <thead><tr><th>#</th><th>Patient</th><th>Blood Group</th><th>Units</th><th>Hospital</th><th>Priority</th><th>Date</th><th>Status</th><th>Action</th></tr></thead>
          <tbody>
          {% for r in requests %}
          <tr>
            <td>#{{ r.id }}</td>
            <td><strong>{{ r.patient }}</strong></td>
            <td><span style="font-family:'Playfair Display',serif;font-weight:900;color:var(--crimson)">{{ r.blood_group }}</span></td>
            <td>{{ r.units }}</td>
            <td>{{ r.hospital }}</td>
            <td><span class="badge priority-{{ r.priority.lower() }}">{{ r.priority }}</span></td>
            <td>{{ r.date }}</td>
            <td><span class="badge {{ 'badge-green' if r.status=='Approved' else 'badge-yellow' }}">{{ r.status }}</span></td>
            <td>
              {% if r.status == 'Pending' %}
              <form method="POST" action="/approve_request/{{ r.id }}" style="display:inline">
                <button type="submit" class="btn btn-success btn-sm">Approve</button>
              </form>
              {% else %}<span style="color:var(--gray);font-size:0.8rem">Done</span>{% endif %}
            </td>
          </tr>
          {% endfor %}
          </tbody>
        </table>
      </div>
    </div>

    <!-- Donors Table -->
    <div class="card">
      <div class="card-body" style="padding-bottom:0">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:1rem">
          <h3 style="font-family:'Playfair Display',serif;font-size:1.2rem;color:var(--navy)">Donor Records</h3>
          <a href="/donate" class="btn btn-outline btn-sm">+ Add Donor</a>
        </div>
      </div>
      <div class="table-wrapper">
        <table>
          <thead><tr><th>#</th><th>Name</th><th>Age</th><th>Gender</th><th>Blood Group</th><th>Phone</th><th>City</th><th>Last Donation</th><th>Total Units</th><th>Status</th></tr></thead>
          <tbody>
          {% for d in donors %}
          <tr>
            <td>#{{ d.id }}</td>
            <td><strong>{{ d.name }}</strong></td>
            <td>{{ d.age }}</td>
            <td>{{ d.gender }}</td>
            <td><span style="font-family:'Playfair Display',serif;font-weight:900;color:var(--crimson)">{{ d.blood_group }}</span></td>
            <td>{{ d.phone }}</td>
            <td>{{ d.city }}</td>
            <td>{{ d.last_donation }}</td>
            <td>{{ d.units }}</td>
            <td><span class="badge badge-green">{{ d.status }}</span></td>
          </tr>
          {% endfor %}
          </tbody>
        </table>
      </div>
    </div>
  </div>
</section>

<script>
const ctx = document.getElementById('stockChart').getContext('2d');
new Chart(ctx, {
  type: 'bar',
  data: {
    labels: {{ labels|tojson }},
    datasets: [{
      label: 'Units Available',
      data: {{ values|tojson }},
      backgroundColor: {{ colors|tojson }},
      borderRadius: 8,
      borderSkipped: false,
    }]
  },
  options: {
    responsive: true, maintainAspectRatio: true,
    plugins: { legend: { display: false } },
    scales: {
      y: { beginAtZero: true, grid: { color: '#f0f0f0' }, ticks: { font: { family: 'DM Sans' } } },
      x: { grid: { display: false }, ticks: { font: { family: 'DM Sans', weight: '600' } } }
    }
  }
});
</script>
<style>@media(max-width:768px){.chart-grid{grid-template-columns:1fr!important}}</style>
"""

# ─── CONTACT PAGE ─────────────────────────────────────────────────────────────
CONTACT_CONTENT = """
<div class="page-header">
  <div class="breadcrumb"><a href="/">Home</a> / Contact</div>
  <h1>📞 Contact Us</h1>
  <p>Get in touch with our blood bank team</p>
</div>

<section class="section">
  <div class="container">
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:2rem;align-items:start" class="contact-grid">
      <div>
        <div class="form-card">
          <h2 style="font-family:'Playfair Display',serif;font-size:1.5rem;color:var(--navy);margin-bottom:1.5rem">Send Us a Message</h2>
          <form method="POST" action="/contact">
            <div class="form-row">
              <div class="form-group">
                <label class="form-label">Full Name</label>
                <input type="text" name="name" class="form-control" placeholder="Your name" required>
              </div>
              <div class="form-group">
                <label class="form-label">Email</label>
                <input type="email" name="email" class="form-control" placeholder="your@email.com" required>
              </div>
            </div>
            <div class="form-group">
              <label class="form-label">Subject</label>
              <select name="subject" class="form-control form-select">
                <option>General Inquiry</option>
                <option>Blood Request</option>
                <option>Donor Registration</option>
                <option>Emergency</option>
                <option>Partnership</option>
              </select>
            </div>
            <div class="form-group">
              <label class="form-label">Message</label>
              <textarea name="message" class="form-control" rows="5" placeholder="Write your message..." required></textarea>
            </div>
            <button type="submit" class="btn btn-primary btn-lg" style="width:100%;justify-content:center">Send Message</button>
          </form>
        </div>
      </div>

      <div>
        <div class="contact-info-card" style="margin-bottom:1.2rem">
          <h3>📍 Main Blood Bank</h3>
          <div class="contact-item">
            <div class="contact-item-icon">📍</div>
            <div style="font-size:0.9rem;opacity:0.85">45, MG Road, Bengaluru, Karnataka 560001</div>
          </div>
          <div class="contact-item">
            <div class="contact-item-icon">📞</div>
            <div style="font-size:0.9rem;opacity:0.85">+91 80 4567 8900<br>+91 80 4567 8901</div>
          </div>
          <div class="contact-item">
            <div class="contact-item-icon">✉</div>
            <div style="font-size:0.9rem;opacity:0.85">info@lifeflow.org<br>emergency@lifeflow.org</div>
          </div>
          <div class="contact-item">
            <div class="contact-item-icon">🕐</div>
            <div style="font-size:0.9rem;opacity:0.85">Mon–Sat: 8 AM – 8 PM<br>Emergency: 24/7</div>
          </div>
          <div class="emergency-numbers">
            <h4>🚨 Emergency Numbers</h4>
            <div class="emg-num"><span>National Blood Line</span><strong>104</strong></div>
            <div class="emg-num"><span>LifeFlow Emergency</span><strong>1800-XXX-XXXX</strong></div>
            <div class="emg-num"><span>Ambulance</span><strong>108</strong></div>
          </div>
        </div>

        <!-- Simple Map placeholder -->
        <div class="card">
          <div style="background:var(--sky);height:220px;display:flex;align-items:center;justify-content:center;flex-direction:column;gap:12px;border-radius:var(--radius-lg)">
            <div style="font-size:3rem">🗺️</div>
            <div style="font-size:0.9rem;color:var(--gray);font-weight:600">Interactive Map</div>
            <div style="font-size:0.8rem;color:var(--gray)">45 MG Road, Bengaluru</div>
            <a href="https://maps.google.com/?q=MG+Road+Bengaluru" target="_blank" class="btn btn-navy btn-sm">Open in Maps</a>
          </div>
        </div>
      </div>
    </div>
  </div>
</section>
<style>@media(max-width:768px){.contact-grid{grid-template-columns:1fr!important}}</style>
"""

# ─── AUTH PAGES ───────────────────────────────────────────────────────────────
LOGIN_CONTENT = """
<div style="min-height:80vh;display:flex;align-items:center;justify-content:center;padding:2rem;background:linear-gradient(135deg,var(--navy),var(--navy-mid))">
  <div style="width:100%;max-width:420px">
    <div class="form-card" style="box-shadow:var(--shadow-lg)">
      <div style="text-align:center;margin-bottom:2rem">
        <div style="font-size:3rem;margin-bottom:0.5rem">🩸</div>
        <h2 style="font-family:'Playfair Display',serif;font-size:1.8rem;color:var(--navy)">Welcome Back</h2>
        <p style="color:var(--gray);font-size:0.9rem">Sign in to your LifeFlow account</p>
      </div>
      <form method="POST" action="/login">
        <div class="form-group">
          <label class="form-label">Username</label>
          <input type="text" name="username" class="form-control" placeholder="Enter username" required>
        </div>
        <div class="form-group">
          <label class="form-label">Password</label>
          <input type="password" name="password" class="form-control" placeholder="Enter password" required>
        </div>
        <button type="submit" class="btn btn-primary btn-lg" style="width:100%;justify-content:center;margin-top:0.5rem">Login</button>
      </form>
      <div style="text-align:center;margin-top:1.2rem;font-size:0.85rem;color:var(--gray)">
        <p>Demo: <code style="background:var(--sky);padding:2px 6px;border-radius:4px">admin / admin123</code></p>
        <p style="margin-top:0.5rem">Don't have an account? <a href="/signup" style="color:var(--crimson);font-weight:600">Sign up</a></p>
      </div>
    </div>
  </div>
</div>
"""

SIGNUP_CONTENT = """
<div style="min-height:80vh;display:flex;align-items:center;justify-content:center;padding:2rem;background:linear-gradient(135deg,var(--navy),var(--navy-mid))">
  <div style="width:100%;max-width:480px">
    <div class="form-card" style="box-shadow:var(--shadow-lg)">
      <div style="text-align:center;margin-bottom:2rem">
        <div style="font-size:3rem;margin-bottom:0.5rem">❤️</div>
        <h2 style="font-family:'Playfair Display',serif;font-size:1.8rem;color:var(--navy)">Create Account</h2>
        <p style="color:var(--gray);font-size:0.9rem">Join the LifeFlow community</p>
      </div>
      <form method="POST" action="/signup">
        <div class="form-row">
          <div class="form-group">
            <label class="form-label">Full Name</label>
            <input type="text" name="name" class="form-control" placeholder="Your name" required>
          </div>
          <div class="form-group">
            <label class="form-label">Username</label>
            <input type="text" name="username" class="form-control" placeholder="Choose username" required>
          </div>
        </div>
        <div class="form-group">
          <label class="form-label">Password</label>
          <input type="password" name="password" class="form-control" placeholder="Create password" required>
        </div>
        <div class="form-group">
          <label class="form-label">Role</label>
          <select name="role" class="form-control form-select">
            <option value="donor">Donor</option>
            <option value="staff">Hospital Staff</option>
          </select>
        </div>
        <button type="submit" class="btn btn-primary btn-lg" style="width:100%;justify-content:center;margin-top:0.5rem">Create Account</button>
      </form>
      <div style="text-align:center;margin-top:1.2rem;font-size:0.85rem;color:var(--gray)">
        Already have an account? <a href="/login" style="color:var(--crimson);font-weight:600">Login</a>
      </div>
    </div>
  </div>
</div>
"""

# ─── RENDER HELPER ────────────────────────────────────────────────────────────
def render(content, page='', **kwargs):
    return render_template_string(
        BASE_HTML.replace('{{ content }}', content),
        page=page,
        blood_inventory=BLOOD_INVENTORY,
        donors=DONORS,
        requests=BLOOD_REQUESTS,
        **kwargs
    )

# ─── ROUTES ──────────────────────────────────────────────────────────────────
@app.route('/')
def home():
    return render(HOME_CONTENT, page='home')

@app.route('/availability')
def availability():
    group = request.args.get('group', '')
    city  = request.args.get('city', '')
    return render(AVAIL_CONTENT, page='avail', selected_group=group, selected_city=city)

@app.route('/donate', methods=['GET','POST'])
def donate():
    global next_donor_id
    if request.method == 'POST':
        DONORS.append({
            'id': next_donor_id,
            'name': request.form['name'],
            'age': int(request.form['age']),
            'gender': request.form['gender'],
            'blood_group': request.form['blood_group'],
            'phone': request.form['phone'],
            'city': request.form.get('city',''),
            'last_donation': request.form.get('last_donation', 'N/A') or 'N/A',
            'units': 0,
            'status': 'Active'
        })
        next_donor_id += 1
        BLOOD_INVENTORY[request.form['blood_group']]['units'] += 1
        flash(f"Thank you {request.form['name']}! Your donor registration is complete. 🩸", 'success')
        return redirect(url_for('home'))
    return render(DONATE_CONTENT, page='donate')

@app.route('/request', methods=['GET','POST'])
def blood_request():
    global next_request_id
    preselect = request.args.get('group','')
    if request.method == 'POST':
        BLOOD_REQUESTS.append({
            'id': next_request_id,
            'patient': request.form['patient'],
            'blood_group': request.form['blood_group'],
            'units': int(request.form['units']),
            'hospital': request.form['hospital'],
            'priority': request.form.get('priority','Normal'),
            'status': 'Pending',
            'date': datetime.now().strftime('%Y-%m-%d')
        })
        next_request_id += 1
        flash(f"Blood request submitted for {request.form['patient']}. Our team will contact you shortly.", 'success')
        return redirect(url_for('blood_request'))
    return render(REQUEST_CONTENT, page='request', preselect_group=preselect)

@app.route('/info')
def info():
    return render(INFO_CONTENT, page='info')

@app.route('/dashboard')
def dashboard():
    if not session.get('user'):
        flash('Please login to access the dashboard.', 'danger')
        return redirect(url_for('login'))
    total_units = sum(d['units'] for d in BLOOD_INVENTORY.values())
    labels = list(BLOOD_INVENTORY.keys())
    values = [d['units'] for d in BLOOD_INVENTORY.values()]
    colors = ['#059669' if v > 30 else ('#D97706' if v > 10 else '#C8102E') for v in values]
    pending = sum(1 for r in BLOOD_REQUESTS if r['status'] == 'Pending')
    approved = sum(1 for r in BLOOD_REQUESTS if r['status'] == 'Approved')
    return render(DASHBOARD_CONTENT, page='dash',
        total_units=total_units, donor_count=len(DONORS),
        pending_count=pending, approved_count=approved,
        labels=labels, values=values, colors=colors)

@app.route('/approve_request/<int:req_id>', methods=['POST'])
def approve_request(req_id):
    if not session.get('user'):
        return redirect(url_for('login'))
    for r in BLOOD_REQUESTS:
        if r['id'] == req_id:
            r['status'] = 'Approved'
            bg = r['blood_group']
            if BLOOD_INVENTORY[bg]['units'] >= r['units']:
                BLOOD_INVENTORY[bg]['units'] -= r['units']
            flash(f"Request #{req_id} approved. Inventory updated.", 'success')
            break
    return redirect(url_for('dashboard'))

@app.route('/contact', methods=['GET','POST'])
def contact():
    if request.method == 'POST':
        flash(f"Message received from {request.form['name']}. We'll respond within 24 hours!", 'success')
        return redirect(url_for('contact'))
    return render(CONTACT_CONTENT, page='contact')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        uname = request.form['username']
        pwd = hashlib.md5(request.form['password'].encode()).hexdigest()
        if uname in USERS and USERS[uname]['password'] == pwd:
            session['user'] = uname
            session['name'] = USERS[uname]['name']
            session['role'] = USERS[uname]['role']
            flash(f"Welcome back, {USERS[uname]['name']}!", 'success')
            return redirect(url_for('dashboard') if USERS[uname]['role']=='staff' else url_for('home'))
        flash('Invalid username or password.', 'danger')
        return redirect(url_for('login'))
    return render(LOGIN_CONTENT, page='login')

@app.route('/signup', methods=['GET','POST'])
def signup():
    if request.method == 'POST':
        uname = request.form['username']
        if uname in USERS:
            flash('Username already exists.', 'danger')
            return redirect(url_for('signup'))
        USERS[uname] = {
            'password': hashlib.md5(request.form['password'].encode()).hexdigest(),
            'role': request.form.get('role','donor'),
            'name': request.form['name']
        }
        session['user'] = uname
        session['name'] = request.form['name']
        session['role'] = request.form.get('role','donor')
        flash(f"Account created! Welcome to LifeFlow, {request.form['name']}! 🩸", 'success')
        return redirect(url_for('home'))
    return render(SIGNUP_CONTENT, page='signup')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('home'))

# ─── API ENDPOINTS (JSON) ─────────────────────────────────────────────────────
@app.route('/api/inventory')
def api_inventory():
    return jsonify(BLOOD_INVENTORY)

@app.route('/api/donors')
def api_donors():
    return jsonify(DONORS)


