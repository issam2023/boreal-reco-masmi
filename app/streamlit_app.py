"""Boréal Marché V4 — visual, explainable grocery recommendation storefront.
Run from project root: streamlit run app/streamlit_app.py
Uses offline JSON rules; never runs Apriori in the web app.
"""
from __future__ import annotations
import json
import re
from pathlib import Path
from html import escape
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
st.set_page_config(page_title="Boréal Marché | Smart Grocery", page_icon="🥬", layout="wide", initial_sidebar_state="collapsed")

st.markdown('''<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito+Sans:wght@400;500;600;700;800;900&display=swap');
html,body,[data-testid="stApp"] {font-family:'Nunito Sans',sans-serif;color:#183c31}
.stApp {background:linear-gradient(125deg,#f7fff8,#f5fbf7 60%,#fefcf3)}
.block-container {max-width:1850px;padding:1rem 1.5rem 4rem}
[data-testid="stHeader"] {background:transparent}
h1,h2,h3 {color:#0b5639!important}
.hero {background:linear-gradient(105deg,#e6fff0 0%,#fff8d7 47%,#d9f8e5 100%);border:1px solid #ccead8;border-radius:24px;padding:22px 30px;box-shadow:0 8px 28px #1a6d3d12;margin-bottom:14px;display:flex;align-items:center;justify-content:space-between;gap:15px}
.hero-title {font-size:2.6rem;font-weight:900;color:#075637;line-height:1.1}
.hero-tag {font-size:.78rem;letter-spacing:.14em;font-weight:900;color:#258355}
.hero-desc {color:#486a56;font-size:.91rem;margin-top:7px}
.hero-art {font-size:3.7rem;letter-spacing:.07em;white-space:nowrap}
.kpi {background:white;border:1px solid #dceee2;border-radius:16px;padding:13px 17px;box-shadow:0 3px 12px #1a59320c}
.kpi-num {font-size:1.65rem;font-weight:900;color:#087449;line-height:1.3}
.kpi-label {font-size:.76rem;color:#5a7668}
.section-head {font-size:1.22rem;font-weight:900;color:#0b5c3c;margin:18px 0 9px}
.sidebox {background:#fff;border:1px solid #d7eee1;border-radius:17px;padding:15px;margin:7px 0 13px;box-shadow:0 4px 16px #246f3d0c}
.howbox {background:#e7faeb;border-radius:16px;padding:15px;line-height:2;color:#205c40;font-size:.89rem}
.product {background:white;border:1px solid #e0ece3;border-radius:17px;padding:12px;box-shadow:0 5px 16px #1b6a3912;min-height:220px}
.product-art {height:128px;display:flex;align-items:center;justify-content:center;border-radius:12px;background:linear-gradient(130deg,#f5fce8,#e3f8ec);font-size:3.7rem;margin-bottom:10px}
.product-photo {width:100%;height:128px;object-fit:cover;border-radius:12px;margin-bottom:10px} 
.product-name {font-weight:900;font-size:.93rem;color:#173e30;min-height:21px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.product-en {font-size:.74rem;color:#6a8075;min-height:20px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.product-category {display:inline-block;border-radius:20px;background:#e8f7ee;color:#197247;font-size:.69rem;padding:3px 9px;margin-top:5px}
.product-price {font-size:1.18rem;font-weight:900;color:#087b48;margin-top:7px}
.basketbox {background:white;border:1px solid #d9e9de;border-radius:14px;padding:11px 13px;margin:6px 0}
.emptybox {background:#effaf5;border:1px dashed #9fd3b5;border-radius:16px;padding:22px 12px;text-align:center;color:#3b7656}
.recobox {background:white;border:1px solid #d4e8da;border-left:5px solid #16a368;border-radius:16px;padding:12px;margin:10px 0 5px;box-shadow:0 5px 15px #246b3e12}
.strength-track{height:9px;background:#e8f1e9;border-radius:20px;overflow:hidden;margin:8px 0 4px}.strength-fill{height:100%;background:linear-gradient(90deg,#3bc77d,#087c51);border-radius:20px}.rec-name {font-weight:900;color:#17533a;font-size:.98rem}
.small-muted {color:#688477;font-size:.76rem}
.chip {display:inline-block;background:#eaf8ed;color:#216a46;border-radius:8px;padding:4px 7px;margin:4px 4px 0 0;font-size:.73rem;font-weight:800}
.chip-gold {background:#fff2ca;color:#855c00}
.stButton>button {border-radius:10px!important;font-weight:800!important;min-height:37px}
.stButton>button[kind="primary"] {background:#078650!important;color:white!important;border-color:#078650!important}
.stButton>button[kind="primary"]:hover {background:#076c43!important}
[data-testid="stTextInput"] input,[data-testid="stSelectbox"]>div>div {border-radius:11px}
[data-testid="stVerticalBlock"] {gap:.5rem}
@media(max-width:850px){.hero-title{font-size:1.8rem}.hero-art{font-size:2rem}.block-container{padding:1rem .7rem}}
</style>''',unsafe_allow_html=True)

@st.cache_data(show_spinner=False)
def load_data():
    p=pd.read_csv(ROOT/'data'/'products.csv')
    required={'Item','Item_EN','Category','Price'}
    if not required.issubset(p.columns):
        raise ValueError(f"Catalogue columns missing: {required-set(p.columns)}")
    def read(name):
        with (ROOT/'models'/name).open(encoding='utf-8') as f:return json.load(f)
    return p,read('rules.json'),read('popularity.json'),read('metadata.json')

try:
    products,rules,popularity,metadata=load_data()
except (OSError,ValueError,json.JSONDecodeError) as e:
    st.error(f'Project files could not be loaded: {e}')
    st.stop()

catalogue={p['Item']:p for p in products.to_dict('records')}
# Store quantities, not duplicate item names. Apriori still uses presence/absence.
if 'basket' not in st.session_state: st.session_state.basket={}
if isinstance(st.session_state.basket,list):
    st.session_state.basket={item:1 for item in st.session_state.basket if item in catalogue}
def add(item):
    if item in catalogue: st.session_state.basket[item]=st.session_state.basket.get(item,0)+1
def remove(item): st.session_state.basket.pop(item,None)
def decrement(item):
    if item in st.session_state.basket:
        st.session_state.basket[item]-=1
        if st.session_state.basket[item]<=0: st.session_state.basket.pop(item,None)
def clear():st.session_state.basket={}
def slug(item):
    import unicodedata
    v=unicodedata.normalize('NFKD',str(item)).encode('ascii','ignore').decode('ascii')
    return re.sub(r'[^a-z0-9]+','-',v.lower()).strip('-')

def product_image(item):
    """Use exact product photo only if supplied locally; never show a wrong product photo."""
    base=ROOT/'app'/'assets'/'products'
    for ext in ('.webp','.jpg','.jpeg','.png'):
        path=base/(slug(item)+ext)
        if path.is_file(): return path
    return None

def safe(x):return escape(str(x),quote=True)
def emoji(category,item=''):
    n=str(item).lower();c=str(category).lower()
    for needle,symbol in [('steak','🥩'),('saucisse','🌭'),('poulet','🍗'),('bacon','🥓'),('saumon','🐟'),('oeuf','🥚'),('œuf','🥚'),('lait','🥛'),('fromage','🧀'),('pomme','🍎'),('banane','🍌'),('tomate','🍅'),('pain','🥖'),('bière','🍺'),('biscuit','🍪'),('sac réutilisable','🛍️'),('noix','🥜'),('beurre d\'arachide','🥜'),('charbon','🔥'),('couche','🍼')]:
        if needle in n:return symbol
    for needle,symbol in [('viande','🥩'),('poisson','🐟'),('laitier','🧀'),('fruit','🍎'),('légume','🥦'),('boisson','🥤'),('bébé','🍼'),('boulanger','🥖'),('épicer','🫙'),('maison','🧼'),('surgel','❄️'),('collation','🍪')]:
        if needle in c:return symbol
    return '🛒'

@st.cache_data(show_spinner=False)
def index_singleton_rules(raw):
    """Only single-product consequents have valid per-product confidence and lift."""
    out=[]
    for r in raw:
        a=r.get('antecedents',[]);c=r.get('consequents',[])
        if len(c)==1 and a and float(r.get('lift',0))>1:
            out.append((frozenset(a),c[0],float(r['support']),float(r['confidence']),float(r['lift'])))
    return out
single_rules=index_singleton_rules(rules)
def recommend(basket,limit=5):
    have=set(basket);best={}
    for antecedents,item,support,confidence,lift in single_rules:
        if not antecedents.issubset(have) or item in have or item not in catalogue:continue
        rec={'item':item,'antecedents':sorted(antecedents),'support':support,'confidence':confidence,'lift':lift}
        if item not in best or (lift,confidence)>(best[item]['lift'],best[item]['confidence']):best[item]=rec
    return sorted(best.values(),key=lambda r:(-r['lift'],-r['confidence'],r['item']))[:limit]
def popular(excluded,limit=5):return [r for r in popularity if r.get('item') in catalogue and r['item'] not in excluded][:limit]
def strength(lift):return 'Very strong' if lift>=5 else 'Strong' if lift>=3 else 'Moderate' if lift>=1.5 else 'Weak'

st.markdown('''<div class="hero"><div><div class="hero-tag">FRESH IDEAS FOR YOUR BASKET</div><div class="hero-title">🛒 Boréal Marché</div><div class="hero-desc">Smart grocery recommendations powered by Apriori association rules</div><div class="hero-desc">Abdelhafid Masmi · Vanier College · 420-975-VA Unsupervised Learning</div></div><div class="hero-art">🥬🍅🥕🧀🥖</div></div>''',unsafe_allow_html=True)
total=sum(float(catalogue[i]['Price'])*qty for i,qty in st.session_state.basket.items())
unit_count=sum(st.session_state.basket.values())
for col,(num,label) in zip(st.columns(4),[(len(products),'Catalogue products'),(f'{len(rules):,}','Association rules'),(f"{float(metadata.get('coverage',0)):.1%}",'Recommendation coverage'),(f'${total:.2f}','Basket total · CAD')]):
    with col:st.markdown(f'<div class="kpi"><div class="kpi-num">{safe(num)}</div><div class="kpi-label">{safe(label)}</div></div>',unsafe_allow_html=True)

side,center,right=st.columns([.9,2.7,1.35],gap='medium')
with side:
    st.markdown('<div class="section-head">🗂️ Categories</div>',unsafe_allow_html=True)
    categories=['All categories']+sorted(products['Category'].dropna().unique().tolist())
    category=st.radio('Select category',categories,format_func=lambda c:f'{emoji(c)} {c} ({len(products) if c=="All categories" else int((products.Category==c).sum())})',label_visibility='collapsed')
    st.markdown('<div class="howbox"><b>💡 How it works</b><div>① Browse the catalogue</div><div>② Add products to your basket</div><div>③ Discover matching recommendations</div><div>④ Explore the Apriori evidence</div></div>',unsafe_allow_html=True)

with center:
    st.markdown('<div class="section-head">🛍️ Explore our products</div>',unsafe_allow_html=True)
    query=st.text_input('Find a product',placeholder='🔎 Search French or English product names…',label_visibility='collapsed')
    c1,c2=st.columns([1.2,1])
    with c1:order=st.selectbox('Sort by',['Catalogue order','Name A → Z','Name Z → A','Price: low to high','Price: high to low'])
    with c2:page_size=st.selectbox('Products per page',[8,12,16],index=0)
    view=products if category=='All categories' else products[products['Category']==category]
    if query.strip():
        q=query.strip();view=view[view['Item'].str.contains(q,case=False,regex=False,na=False)|view['Item_EN'].str.contains(q,case=False,regex=False,na=False)]
    if order=='Name A → Z':view=view.sort_values('Item')
    elif order=='Name Z → A':view=view.sort_values('Item',ascending=False)
    elif order=='Price: low to high':view=view.sort_values('Price')
    elif order=='Price: high to low':view=view.sort_values('Price',ascending=False)
    pages=max(1,(len(view)+page_size-1)//page_size)
    page=st.number_input('Page',min_value=1,max_value=pages,value=1,step=1)
    st.caption(f'{len(view)} products found · Page {page} of {pages}')
    shown=view.iloc[(page-1)*page_size:page*page_size].to_dict('records')
    if not shown:st.info('No products match your search. Try another name or category.')
    for start in range(0,len(shown),4):
        cols=st.columns(4,gap='small')
        for col,p in zip(cols,shown[start:start+4]):
            with col:
                item=p['Item'];added=item in st.session_state.basket
                photo=product_image(item)
                art=(f'<img class="product-photo" src="data:image/{photo.suffix.lstrip(".")};base64,{__import__("base64").b64encode(photo.read_bytes()).decode()}" alt="{safe(item)}">' if photo else f'<div class="product-art">{emoji(p["Category"],item)}</div>')
                st.markdown(f'<div class="product">{art}<div class="product-name" title="{safe(item)}">{safe(item)}</div><div class="product-en" title="{safe(p["Item_EN"])}">{safe(p["Item_EN"])}</div><span class="product-category">{safe(p["Category"])}</span><div class="product-price">${float(p["Price"]):.2f}</div></div>',unsafe_allow_html=True)
                st.button(f'＋ Add another ({st.session_state.basket[item]})' if added else '＋ Add to basket',key=f'catalog_{item}',on_click=add,args=(item,),type='primary',use_container_width=True)

with right:
    st.markdown(f'<div class="section-head">🧺 Your basket ({unit_count} items)</div>',unsafe_allow_html=True)
    if not st.session_state.basket:
        st.markdown('<div class="emptybox"><div style="font-size:2.5rem">🛒</div><b>Your basket is empty!</b><div>Choose products to unlock personalized suggestions.</div></div>',unsafe_allow_html=True)
    else:
        for item,qty in list(st.session_state.basket.items()):
            p=catalogue[item]
            st.markdown(f'<div class="basketbox"><b>{emoji(p["Category"],item)} {safe(item)}</b><div class="small-muted">${float(p["Price"]):.2f} each · {safe(p["Category"])}</div><b style="color:#087b48">Line total: ${float(p["Price"])*qty:.2f}</b></div>',unsafe_allow_html=True)
            a,b,c,d=st.columns([1,1,1,1.5],gap='small')
            with a: st.button('−',key=f'minus_{item}',on_click=decrement,args=(item,),use_container_width=True)
            with b: st.markdown(f'<div style="text-align:center;padding-top:8px;font-weight:900">{qty}</div>',unsafe_allow_html=True)
            with c: st.button('＋',key=f'plus_{item}',on_click=add,args=(item,),use_container_width=True)
            with d: st.button('Remove',key=f'remove_{item}',on_click=remove,args=(item,),use_container_width=True)
        st.success(f'🧾 **Basket total: ${total:.2f} CAD** · {unit_count} units')
        st.button('🗑️ Clear basket',on_click=clear,use_container_width=True)
    st.markdown('<div class="section-head">✨ Recommended for you</div>',unsafe_allow_html=True)
    chosen=recommend(st.session_state.basket.keys())
    if not st.session_state.basket:st.info('Popular products shown until you add something to your basket.')
    elif not chosen:
        st.warning('No matching rule for this basket. Showing popular products instead.')
        if len(st.session_state.basket)==1:
            item=next(iter(st.session_state.basket));pop=next((p for p in popularity if p.get('item')==item),None)
            if pop and float(pop.get('support',1))<float(metadata.get('min_support',0)):
                st.caption(f'Rare product: {item} appears in {float(pop["support"]):.3%} of baskets, below the {float(metadata["min_support"]):.2%} minimum support threshold.')
    if chosen:
        for r in chosen:
            item=r['item'];p=catalogue[item];why=', '.join(r['antecedents'])
            st.markdown(f'<div class="recobox"><div class="rec-name">{emoji(p["Category"],item)} {safe(item)} · ${float(p["Price"]):.2f}</div><div class="small-muted">{safe(p["Item_EN"])} · {safe(p["Category"])}</div><div style="font-size:.83rem;margin-top:8px">Because your basket contains <b>{safe(why)}</b>, customers with those items also buy <b>{safe(item)}</b> <b>{r["confidence"]:.1%}</b> of the time — <b>{r["lift"]:.2f}×</b> the average rate.</div><span class="chip chip-gold">⭐ {strength(r["lift"])}</span><div class="strength-track"><div class="strength-fill" style="width:{min(100,max(0,r['confidence']*100)):.1f}%"></div></div><div class="small-muted">Confidence: {r['confidence']:.1%} · Lift: {r['lift']:.2f}×</div><span class="chip">Support {r["support"]:.2%}</span><span class="chip">Confidence {r["confidence"]:.1%}</span><span class="chip">Lift {r["lift"]:.2f}×</span></div>',unsafe_allow_html=True)
            st.button(f'＋ Add {item}',key=f'reco_{item}',on_click=add,args=(item,),type='primary',use_container_width=True)
    else:
        for p in popular(set(st.session_state.basket)):
            item=p['item'];c=catalogue[item]
            st.markdown(f'<div class="recobox"><div class="rec-name">{emoji(c["Category"],item)} {safe(item)} · ${float(c["Price"]):.2f}</div><div class="small-muted">{safe(c["Item_EN"])} · {safe(c["Category"])}</div><span class="chip chip-gold">🔥 Popular choice</span><span class="chip">In {float(p["support"]):.1%} of baskets</span></div>',unsafe_allow_html=True)
            st.button(f'＋ Add {item}',key=f'popular_{item}',on_click=add,args=(item,),use_container_width=True)
        st.caption('Popularity fallback — not association-rule recommendations.')
    with st.expander('🔍 Rules that fired · Audit trail'):
        if chosen:
            df=pd.DataFrame([{'If basket contains':', '.join(r['antecedents']),'Then suggest':r['item'],'Support':r['support'],'Confidence':r['confidence'],'Lift':r['lift']} for r in chosen])
            st.dataframe(df,hide_index=True,use_container_width=True)
            st.caption('Highest-lift qualifying singleton-consequent rule per suggested product.')
        else:st.write('No qualifying recommendation rules currently fire.')

st.divider()
st.caption('📷 Product photos: place correctly named .jpg/.png/.webp files in app/assets/products/ (e.g., steak-de-boeuf.jpg). Products without photos display illustrated category icons. This prevents misleading product images.')
with st.expander('📘 Methodology, limitations and reproducibility'):
    st.markdown(f'''**Offline mining:** Apriori runs in the notebook; this application only loads exported JSON rules.

**Thresholds:** minimum support {metadata.get('min_support','N/A')}, minimum confidence {metadata.get('min_confidence','N/A')}, lift strictly greater than 1.

**Matching:** All antecedent items must be in the basket. Already selected products are never recommended. When two rules suggest the same product, the highest-lift rule wins.

**Metric integrity:** Rules with multiple consequents are excluded from individual-product suggestions; their joint confidence and lift cannot be attributed to just one consequent.

**Fallbacks:** Empty baskets and baskets with no matching rules show popular products. Very rare products may be absent from all frequent itemsets.

**Limitations:** Association does not prove causation; popularity bias and support thresholds reduce coverage. Quantities affect basket totals, but rule matching uses product presence only. Strength labels are descriptive, not statistical significance tests.''')
