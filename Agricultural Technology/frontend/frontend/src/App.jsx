import { useEffect, useState } from 'react';
import axios from 'axios';
import { Circle, MapContainer, Marker, Popup, TileLayer, useMapEvents } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import './App.css';

delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api').replace(/\/$/, '');
const BUYER_LOCATION = [23.8103, 90.4125];

const api = axios.create({ baseURL: API_BASE_URL });

function getErrorMessage(error) {
  const data = error.response?.data;
  if (typeof data === 'string') return data;
  if (data?.detail) return data.detail;
  if (data?.error) return data.error;
  if (data && typeof data === 'object') {
    const firstError = Object.values(data).flat(Infinity).find((value) => typeof value === 'string');
    if (firstError) return firstError;
  }
  return error.message || 'The request could not be completed. Please try again.';
}

function LocationPicker({ onLocationSelect }) {
  useMapEvents({
    click(event) {
      onLocationSelect(event.latlng.lat, event.latlng.lng);
    },
  });
  return null;
}

export default function App() {
  const [activeTab, setActiveTab] = useState('buyer');
  const [radius, setRadius] = useState(30);
  const [crops, setCrops] = useState([]);
  const [cropsLoading, setCropsLoading] = useState(true);
  const [cropsError, setCropsError] = useState('');
  const [refreshCrops, setRefreshCrops] = useState(0);
  const totalTonnage = crops.reduce((total, crop) => {
    const quantity = Number(crop.total_quantity);
    return total + (Number.isFinite(quantity) ? quantity : 0);
  }, 0) / 1000;
  const listedPrices = crops
    .map((crop) => Number(crop.price_per_kg))
    .filter((price) => Number.isFinite(price) && price > 0);
  const averagePrice = listedPrices.length
    ? listedPrices.reduce((total, price) => total + price, 0) / listedPrices.length
    : null;
  const identifiedGrowers = new Set(
    crops.map((crop) => crop.farmer_name?.trim()).filter(Boolean),
  ).size;

  const [accessToken, setAccessToken] = useState(() => localStorage.getItem('agritech_access_token'));
  const [account, setAccount] = useState(() => {
    const fullName = localStorage.getItem('agritech_full_name');
    const role = localStorage.getItem('agritech_role');
    return fullName && role ? { fullName, role } : null;
  });
  const [authMode, setAuthMode] = useState('');
  const [authForm, setAuthForm] = useState({
    phone_number: '',
    full_name: '',
    password: '',
    role: 'FARMER',
    business_name: '',
    address: '',
  });
  const [authError, setAuthError] = useState('');
  const [authBusy, setAuthBusy] = useState(false);

  const [farmerForm, setFarmerForm] = useState({
    crop_name: '',
    total_quantity: '',
    price_per_kg: '',
    latitude: 23.82,
    longitude: 90.41,
  });
  const [farmerMessage, setFarmerMessage] = useState('');
  const [farmerError, setFarmerError] = useState('');
  const [farmerBusy, setFarmerBusy] = useState(false);

  const [selectedCrop, setSelectedCrop] = useState(null);
  const [bidForm, setBidForm] = useState({
    buyer_name: '',
    buyer_phone: '',
    offered_price_per_kg: '',
    requested_quantity: '',
  });
  const [bidMessage, setBidMessage] = useState('');
  const [bidError, setBidError] = useState('');
  const [bidBusy, setBidBusy] = useState(false);

  const [offers, setOffers] = useState([]);
  const [offersLoading, setOffersLoading] = useState(false);
  const [offersError, setOffersError] = useState('');
  const [refreshOffers, setRefreshOffers] = useState(0);
  const [actionBusy, setActionBusy] = useState(null);

  useEffect(() => {
    const controller = new AbortController();
    api.get('/listings/nearby/', {
      params: { lat: BUYER_LOCATION[0], lng: BUYER_LOCATION[1], radius },
      signal: controller.signal,
    }).then(({ data }) => {
      setCrops(data);
      setCropsError('');
      setCropsLoading(false);
    }).catch((error) => {
      if (error.code === 'ERR_CANCELED') return;
      setCropsError(getErrorMessage(error));
      setCropsLoading(false);
    });
    return () => controller.abort();
  }, [radius, refreshCrops]);

  useEffect(() => {
    if (activeTab !== 'offers' || !accessToken) return undefined;
    const controller = new AbortController();
    api.get('/negotiations/offers/', {
      headers: { Authorization: `Bearer ${accessToken}` },
      signal: controller.signal,
    }).then(({ data }) => {
      setOffers(data);
      setOffersError('');
      setOffersLoading(false);
    }).catch((error) => {
      if (error.code === 'ERR_CANCELED') return;
      setOffersError(getErrorMessage(error));
      setOffersLoading(false);
    });
    return () => controller.abort();
  }, [activeTab, accessToken, refreshOffers]);

  function changeTab(tab) {
    setActiveTab(tab);
    if (tab === 'buyer') setCropsLoading(true);
    if (tab === 'offers' && accessToken) setOffersLoading(true);
  }

  function openAuth(mode) {
    setAuthError('');
    setAuthMode(mode);
  }

  function saveSession(tokens, user) {
    localStorage.setItem('agritech_access_token', tokens.access);
    if (tokens.refresh) localStorage.setItem('agritech_refresh_token', tokens.refresh);
    localStorage.setItem('agritech_full_name', user.full_name);
    localStorage.setItem('agritech_role', user.role);
    setAccessToken(tokens.access);
    setAccount({ fullName: user.full_name, role: user.role });
  }

  async function handleAuthSubmit(event) {
    event.preventDefault();
    setAuthError('');
    setAuthBusy(true);
    try {
      if (authMode === 'register') {
        await api.post('/auth/register/', {
          ...authForm,
          latitude: BUYER_LOCATION[0],
          longitude: BUYER_LOCATION[1],
        });
      }
      const { data: tokens } = await api.post('/auth/login/', {
        phone_number: authForm.phone_number,
        password: authForm.password,
      });
      saveSession(tokens, {
        full_name: tokens.full_name,
        role: tokens.role,
      });
      setAuthMode('');
      setAuthForm({
        phone_number: '',
        full_name: '',
        password: '',
        role: 'FARMER',
        business_name: '',
        address: '',
      });
      if (activeTab === 'offers') setOffersLoading(true);
    } catch (error) {
      setAuthError(getErrorMessage(error));
    } finally {
      setAuthBusy(false);
    }
  }

  function handleLogout() {
    localStorage.removeItem('agritech_access_token');
    localStorage.removeItem('agritech_refresh_token');
    localStorage.removeItem('agritech_full_name');
    localStorage.removeItem('agritech_role');
    setAccessToken(null);
    setAccount(null);
    setOffers([]);
    changeTab('buyer');
  }

  async function handleFarmerSubmit(event) {
    event.preventDefault();
    setFarmerMessage('');
    setFarmerError('');
    setFarmerBusy(true);
    try {
      await api.post('/listings/create/', {
        ...farmerForm,
      }, {
        headers: { Authorization: `Bearer ${accessToken}` },
      });
      setFarmerMessage('Your harvest is now listed in the marketplace.');
      setFarmerForm((current) => ({
        ...current,
        crop_name: '',
        total_quantity: '',
        price_per_kg: '',
      }));
      setRefreshCrops((current) => current + 1);
    } catch (error) {
      setFarmerError(getErrorMessage(error));
    } finally {
      setFarmerBusy(false);
    }
  }

  async function handleBidSubmit(event) {
    event.preventDefault();
    if (!selectedCrop) return;
    setBidBusy(true);
    setBidError('');
    setBidMessage('');
    try {
      await api.post('/negotiations/bid/', {
        listing_id: selectedCrop.id,
        ...bidForm,
      });
      setBidMessage('Your offer was sent to the farmer.');
      setRefreshOffers((current) => current + 1);
      setBidForm({
        buyer_name: '',
        buyer_phone: '',
        offered_price_per_kg: '',
        requested_quantity: '',
      });
    } catch (error) {
      setBidError(getErrorMessage(error));
    } finally {
      setBidBusy(false);
    }
  }

  async function handleBidAction(bidId, action) {
    setActionBusy(bidId);
    setOffersError('');
    try {
      await api.post('/negotiations/offers/', { bid_id: bidId, action }, {
        headers: { Authorization: `Bearer ${accessToken}` },
      });
      setOffers((current) => current.map((offer) => (
        offer.id === bidId ? { ...offer, status: action } : offer
      )));
    } catch (error) {
      setOffersError(getErrorMessage(error));
    } finally {
      setActionBusy(null);
    }
  }

  return (
    <main className="app-shell">
      <header className="app-header">
        <div className="brand">
          <span className="brand-icon" aria-hidden="true">🌾</span>
          <div>
            <h1>Smart Agritech Matchmaker</h1>
            <p>Connecting farmers and local buyers</p>
          </div>
        </div>
        <div className="header-actions">
          <nav className="main-nav" aria-label="Main navigation">
            <button className={activeTab === 'buyer' ? 'nav-button active' : 'nav-button'} onClick={() => changeTab('buyer')}>Buyer map</button>
            <button className={activeTab === 'farmer' ? 'nav-button active' : 'nav-button'} onClick={() => changeTab('farmer')}>Post harvest</button>
            <button className={activeTab === 'offers' ? 'nav-button active' : 'nav-button'} onClick={() => changeTab('offers')}>Offers inbox</button>
          </nav>
          {account ? (
            <div className="account-controls">
              <span className="account-name">{account.fullName}</span>
              <button className="button button-outline button-small" onClick={handleLogout}>Log out</button>
            </div>
          ) : (
            <button className="button button-light button-small" onClick={() => openAuth('login')}>Farmer sign in</button>
          )}
        </div>
      </header>

      {activeTab === 'buyer' && (
        <section className="buyer-layout">
          <section className="supply-analytics" aria-label="Nearby supply analytics">
            <div className="analytics-heading">
              <span className="analytics-icon" aria-hidden="true">▥</span>
              <div>
                <span className="eyebrow">LIVE MARKET SNAPSHOT</span>
                <h2>Nearby supply pipeline</h2>
                <p>Based on listings within your {radius} km search radius</p>
              </div>
            </div>
            <div className="analytics-metrics" aria-live="polite">
              <div className="analytics-metric">
                <span>Available supply</span>
                <strong>
                  {cropsLoading ? '…' : cropsError ? '—' : `${totalTonnage.toFixed(1)} t`}
                </strong>
              </div>
              <div className="analytics-metric">
                <span>Average listed price</span>
                <strong>
                  {cropsLoading ? '…' : cropsError ? '—' : averagePrice === null
                    ? '—'
                    : `৳${averagePrice.toFixed(1)}/kg`}
                </strong>
              </div>
              <div className="analytics-metric">
                <span>Identified growers</span>
                <strong>{cropsLoading ? '…' : cropsError ? '—' : identifiedGrowers}</strong>
              </div>
            </div>
            <span className={`analytics-status${cropsError ? ' analytics-status-error' : ''}`}>
              <span aria-hidden="true">●</span>
              {cropsLoading ? 'Updating nearby data' : cropsError ? 'Data unavailable' : 'Nearby matching active'}
            </span>
          </section>
          <aside className="panel listings-panel">
            <div className="panel-heading">
              <div>
                <span className="eyebrow">MARKETPLACE</span>
                <h2>Nearby harvests</h2>
              </div>
              <button
                className="icon-button"
                aria-label="Refresh nearby harvests"
                title="Refresh"
                onClick={() => {
                  setCropsLoading(true);
                  setRefreshCrops((current) => current + 1);
                }}
              >↻</button>
            </div>
            <label className="range-label" htmlFor="radius">
              Search radius <strong>{radius} km</strong>
            </label>
            <input
              id="radius"
              className="radius-slider"
              type="range"
              min="5"
              max="100"
              value={radius}
              onChange={(event) => {
                setRadius(Number(event.target.value));
                setCropsLoading(true);
              }}
            />
            <div className="listing-count">{crops.length} {crops.length === 1 ? 'listing' : 'listings'} found</div>
            <div className="listing-scroll">
              {cropsLoading && <p className="empty-state">Searching for nearby harvests…</p>}
              {!cropsLoading && cropsError && (
                <div className="notice notice-error">
                  <strong>Could not load listings.</strong>
                  <span>{cropsError}</span>
                  <span>Check that the backend is running, then refresh.</span>
                </div>
              )}
              {!cropsLoading && !cropsError && crops.length === 0 && (
                <p className="empty-state">No harvests in this radius yet. Try a wider search or check back later.</p>
              )}
              {!cropsLoading && !cropsError && crops.map((crop) => (
                <article className="listing-card" key={crop.id}>
                  <div className="listing-card-top">
                    <h3>{crop.crop_name}</h3>
                    <span className="distance-chip">{crop.distance_km} km</span>
                  </div>
                  <p className="listing-farmer">Farmer: {crop.farmer_name || 'Local farmer'}</p>
                  <div className="listing-meta">
                    <span>{Number(crop.total_quantity).toLocaleString()} kg available</span>
                    <strong>৳{Number(crop.price_per_kg).toLocaleString()}<small>/kg</small></strong>
                  </div>
                  <button className="button button-primary button-full" onClick={() => {
                    setSelectedCrop(crop);
                    setBidError('');
                    setBidMessage('');
                  }}>
                    Send an offer
                  </button>
                </article>
              ))}
            </div>
          </aside>
          <div className="map-panel" aria-label="Map of nearby harvest listings">
            <MapContainer center={BUYER_LOCATION} zoom={9} className="map-canvas">
              <TileLayer
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              />
              <Marker position={BUYER_LOCATION}>
                <Popup><strong>Buyer search center</strong></Popup>
              </Marker>
              <Circle
                center={BUYER_LOCATION}
                radius={radius * 1000}
                pathOptions={{ color: '#16845b', fillColor: '#39a978', fillOpacity: 0.13 }}
              />
              {crops.map((crop) => (
                <Marker key={crop.id} position={[crop.latitude, crop.longitude]}>
                  <Popup>
                    <strong>{crop.crop_name}</strong><br />
                    {crop.total_quantity} kg · ৳{crop.price_per_kg}/kg<br />
                    {crop.farmer_name} · {crop.distance_km} km
                  </Popup>
                </Marker>
              ))}
            </MapContainer>
          </div>
        </section>
      )}

      {activeTab === 'farmer' && (
        <section className="workspace-panel">
          {account?.role !== 'FARMER' ? (
            <div className="gate-card">
              <span className="gate-icon">🚜</span>
              <h2>Farmer account required</h2>
              <p>Sign in or create a farmer account to publish harvests and manage offers.</p>
              <button className="button button-primary" onClick={() => openAuth(account ? 'login' : 'register')}>
                {account ? 'Switch account' : 'Create farmer account'}
              </button>
            </div>
          ) : (
            <div className="form-layout">
              <section className="panel form-panel">
                <span className="eyebrow">FARMER MARKETPLACE</span>
                <h2>Post a harvest</h2>
                <p className="form-intro">Tell local buyers what you have available.</p>
                {farmerMessage && <div className="notice notice-success">{farmerMessage}</div>}
                {farmerError && <div className="notice notice-error">{farmerError}</div>}
                <form className="stacked-form" onSubmit={handleFarmerSubmit}>
                  <label>
                    Crop name
                    <input
                      required
                      maxLength="100"
                      value={farmerForm.crop_name}
                      placeholder="e.g. Red tomatoes"
                      onChange={(event) => setFarmerForm({ ...farmerForm, crop_name: event.target.value })}
                    />
                  </label>
                  <div className="form-two-columns">
                    <label>
                      Available quantity (kg)
                      <input
                        required
                        type="number"
                        min="0.01"
                        step="any"
                        value={farmerForm.total_quantity}
                        onChange={(event) => setFarmerForm({ ...farmerForm, total_quantity: event.target.value })}
                      />
                    </label>
                    <label>
                      Price per kg (BDT)
                      <input
                        required
                        type="number"
                        min="0.01"
                        step="any"
                        value={farmerForm.price_per_kg}
                        onChange={(event) => setFarmerForm({ ...farmerForm, price_per_kg: event.target.value })}
                      />
                    </label>
                  </div>
                  <label>
                    Farm coordinates <span className="field-hint">Click the map to set the pin</span>
                    <input readOnly value={`${farmerForm.latitude.toFixed(4)}, ${farmerForm.longitude.toFixed(4)}`} />
                  </label>
                  <button className="button button-primary button-full" type="submit" disabled={farmerBusy}>
                    {farmerBusy ? 'Publishing…' : 'Publish harvest'}
                  </button>
                </form>
              </section>
              <div className="map-panel farmer-map">
                <MapContainer center={[farmerForm.latitude, farmerForm.longitude]} zoom={10} className="map-canvas">
                  <TileLayer
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                  />
                  <LocationPicker onLocationSelect={(latitude, longitude) => setFarmerForm((current) => ({
                    ...current,
                    latitude,
                    longitude,
                  }))} />
                  <Marker position={[farmerForm.latitude, farmerForm.longitude]}>
                    <Popup>Farm location — click the map to move the pin.</Popup>
                  </Marker>
                </MapContainer>
              </div>
            </div>
          )}
        </section>
      )}

      {activeTab === 'offers' && (
        <section className="panel offers-panel">
          {account?.role !== 'FARMER' ? (
            <div className="gate-card">
              <span className="gate-icon">💬</span>
              <h2>Sign in to view farmer offers</h2>
              <p>The inbox only shows offers for your own harvest listings.</p>
              <button className="button button-primary" onClick={() => openAuth(account ? 'login' : 'login')}>Farmer sign in</button>
            </div>
          ) : (
            <>
              <div className="panel-heading">
                <div>
                  <span className="eyebrow">YOUR LISTINGS</span>
                  <h2>Negotiation inbox</h2>
                </div>
                <button
                  className="button button-outline"
                  onClick={() => {
                    setOffersLoading(true);
                    setRefreshOffers((current) => current + 1);
                  }}
                  disabled={offersLoading}
                >{offersLoading ? 'Refreshing…' : 'Refresh offers'}</button>
              </div>
              {offersError && <div className="notice notice-error">{offersError}</div>}
              {offersLoading ? (
                <p className="empty-state">Loading your offers…</p>
              ) : offers.length === 0 ? (
                <p className="empty-state">No offers for your listings yet. New buyer offers will appear here.</p>
              ) : (
                <div className="offers-grid">
                  {offers.map((offer) => (
                    <article className="offer-card" key={offer.id}>
                      <div className="listing-card-top">
                        <h3>{offer.crop_name}</h3>
                        <span className={`status-chip status-${offer.status.toLowerCase()}`}>{offer.status}</span>
                      </div>
                      <p className="listing-farmer">Offer from <strong>{offer.buyer_name}</strong> · {offer.buyer_phone}</p>
                      <div className="offer-details">
                        <span>Requested quantity</span><strong>{Number(offer.requested_quantity).toLocaleString()} kg</strong>
                        <span>Your listed price</span><strong>৳{Number(offer.original_price).toLocaleString()}/kg</strong>
                        <span>Buyer offer</span><strong className="offer-price">৳{Number(offer.offered_price).toLocaleString()}/kg</strong>
                      </div>
                      <p className="offer-time">Received {offer.created_at}</p>
                      {offer.status === 'PENDING' && (
                        <div className="offer-actions">
                          <button
                            className="button button-accept"
                            onClick={() => handleBidAction(offer.id, 'ACCEPTED')}
                            disabled={actionBusy !== null}
                          >{actionBusy === offer.id ? 'Saving…' : 'Accept offer'}</button>
                          <button
                            className="button button-reject"
                            onClick={() => handleBidAction(offer.id, 'REJECTED')}
                            disabled={actionBusy !== null}
                          >Reject</button>
                        </div>
                      )}
                    </article>
                  ))}
                </div>
              )}
            </>
          )}
        </section>
      )}

      {selectedCrop && (
        <div className="modal-backdrop" role="presentation" onMouseDown={(event) => {
          if (event.target === event.currentTarget && !bidBusy) setSelectedCrop(null);
        }}>
          <section className="modal-card" role="dialog" aria-modal="true" aria-labelledby="bid-title">
            <button className="modal-close" aria-label="Close dialog" onClick={() => setSelectedCrop(null)}>×</button>
            <span className="eyebrow">MAKE AN OFFER</span>
            <h2 id="bid-title">Negotiate {selectedCrop.crop_name}</h2>
            <p className="form-intro">Listed at ৳{Number(selectedCrop.price_per_kg).toLocaleString()}/kg · {Number(selectedCrop.total_quantity).toLocaleString()} kg available</p>
            {bidMessage ? (
              <div className="notice notice-success bid-result">
                {bidMessage}
                <button className="button button-primary" onClick={() => setSelectedCrop(null)}>Done</button>
              </div>
            ) : (
              <form className="stacked-form" onSubmit={handleBidSubmit}>
                {bidError && <div className="notice notice-error">{bidError}</div>}
                <label>
                  Your name / business
                  <input required maxLength="100" value={bidForm.buyer_name} onChange={(event) => setBidForm({ ...bidForm, buyer_name: event.target.value })} />
                </label>
                <label>
                  Phone number
                  <input required maxLength="20" type="tel" value={bidForm.buyer_phone} onChange={(event) => setBidForm({ ...bidForm, buyer_phone: event.target.value })} />
                </label>
                <div className="form-two-columns">
                  <label>
                    Offer per kg (BDT)
                    <input required type="number" min="0.01" step="any" value={bidForm.offered_price_per_kg} onChange={(event) => setBidForm({ ...bidForm, offered_price_per_kg: event.target.value })} />
                  </label>
                  <label>
                    Quantity (kg)
                    <input required type="number" min="0.01" max={selectedCrop.total_quantity} step="any" value={bidForm.requested_quantity} onChange={(event) => setBidForm({ ...bidForm, requested_quantity: event.target.value })} />
                  </label>
                </div>
                <button className="button button-primary button-full" type="submit" disabled={bidBusy}>
                  {bidBusy ? 'Sending offer…' : 'Send offer'}
                </button>
              </form>
            )}
          </section>
        </div>
      )}

      {authMode && (
        <div className="modal-backdrop" role="presentation" onMouseDown={(event) => {
          if (event.target === event.currentTarget && !authBusy) setAuthMode('');
        }}>
          <section className="modal-card" role="dialog" aria-modal="true" aria-labelledby="auth-title">
            <button className="modal-close" aria-label="Close dialog" onClick={() => setAuthMode('')}>×</button>
            <span className="eyebrow">FARMER PORTAL</span>
            <h2 id="auth-title">{authMode === 'register' ? 'Create your farmer account' : 'Farmer sign in'}</h2>
            {authError && <div className="notice notice-error">{authError}</div>}
            <form className="stacked-form" onSubmit={handleAuthSubmit}>
              {authMode === 'register' && (
                <>
                  <label>
                    Full name
                    <input required maxLength="100" value={authForm.full_name} onChange={(event) => setAuthForm({ ...authForm, full_name: event.target.value })} />
                  </label>
                  <label>
                    Farm / business name
                    <input maxLength="150" value={authForm.business_name} onChange={(event) => setAuthForm({ ...authForm, business_name: event.target.value })} />
                  </label>
                  <label>
                    Address
                    <input required value={authForm.address} onChange={(event) => setAuthForm({ ...authForm, address: event.target.value })} />
                  </label>
                </>
              )}
              <label>
                Phone number
                <input required maxLength="15" type="tel" value={authForm.phone_number} onChange={(event) => setAuthForm({ ...authForm, phone_number: event.target.value })} />
              </label>
              <label>
                Password
                <input required type="password" value={authForm.password} onChange={(event) => setAuthForm({ ...authForm, password: event.target.value })} />
              </label>
              <button className="button button-primary button-full" type="submit" disabled={authBusy}>
                {authBusy ? 'Please wait…' : authMode === 'register' ? 'Create account' : 'Sign in'}
              </button>
            </form>
            <p className="auth-switch">
              {authMode === 'register' ? 'Already have a farmer account?' : 'New to the marketplace?'}
              {' '}
              <button onClick={() => {
                setAuthError('');
                setAuthMode(authMode === 'register' ? 'login' : 'register');
              }}>{authMode === 'register' ? 'Sign in' : 'Create an account'}</button>

            </p>
          </section>
        </div>
      )}
    </main>
  );
}

