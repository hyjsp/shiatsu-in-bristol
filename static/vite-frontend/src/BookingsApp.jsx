import React, { useState, useEffect } from 'react';
import { createRoot } from 'react-dom/client';
import 'bootstrap/dist/css/bootstrap.min.css';

console.log('BookingsApp loaded');

const SESSION_LENGTHS = [30, 60, 90];
const API_URL = '/api/bookings/slots/';
const WEEKDAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']; // No Sunday
const SLOT_HOURS = Array.from({ length: 9 }, (_, i) => 9 + i); // 9, 10, 11, 12, 13, 14, 15, 16, 17

function getMonday(date) {
  // Returns the Monday of the week for a given date
  const d = new Date(date);
  const day = d.getDay();
  const diff = d.getDate() - day + (day === 0 ? -6 : 1); // adjust when day is Sunday
  return new Date(d.setDate(diff));
}

function formatDate(date) {
  return date.toISOString().slice(0, 10);
}

function addDays(date, days) {
  const d = new Date(date);
  d.setDate(d.getDate() + days);
  return d;
}

// Helper to get CSRF token from cookie
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

function BookingsApp() {
  const [step, setStep] = useState(1);
  const [selectedLength, setSelectedLength] = useState(null);
  const [selectedSlot, setSelectedSlot] = useState(null);
  const [weekStart, setWeekStart] = useState(() => getMonday(new Date()));
  const [slots, setSlots] = useState([]);
  const [loadingSlots, setLoadingSlots] = useState(false);
  const [slotError, setSlotError] = useState(null);
  const [notes, setNotes] = useState('');
  const [notesError, setNotesError] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [submitSuccess, setSubmitSuccess] = useState(false);
  const [submitError, setSubmitError] = useState('');

  // Fetch slots when length or weekStart changes
  useEffect(() => {
    if (!selectedLength) return;
    setLoadingSlots(true);
    setSlotError(null);
    fetch(`${API_URL}?length=${selectedLength}&week_start=${formatDate(weekStart)}`)
      .then(res => res.json())
      .then(data => {
        setSlots(data.slots || []);
        setLoadingSlots(false);
      })
      .catch(err => {
        setSlotError('Failed to load slots.');
        setLoadingSlots(false);
      });
  }, [selectedLength, weekStart]);

  // Handlers
  const handleLengthSelect = (length) => {
    setSelectedLength(length);
    setStep(2);
    setSelectedSlot(null);
  };

  const handlePrevWeek = () => {
    setWeekStart(addDays(weekStart, -7));
    setSelectedSlot(null);
  };
  const handleNextWeek = () => {
    setWeekStart(addDays(weekStart, 7));
    setSelectedSlot(null);
  };

  const handleSlotSelect = (slot) => {
    if (!slot.reserved) {
      setSelectedSlot(slot);
      setStep(3);
    }
  };

  // Notes validation
  const NOTES_MAX = 1000;
  useEffect(() => {
    if (notes.length > NOTES_MAX) {
      setNotesError(`Notes cannot exceed ${NOTES_MAX} characters.`);
    } else {
      setNotesError('');
    }
  }, [notes]);

  // Booking submission handler (API call)
  const handleBookingSubmit = async (e) => {
    e.preventDefault();
    if (!selectedSlot || notes.length > NOTES_MAX) return;
    // Check authentication
    if (typeof window !== 'undefined' && !window.USER_IS_AUTHENTICATED) {
      // Redirect to login with next param
      window.location.href = `/accounts/login/?next=${encodeURIComponent(window.location.pathname)}`;
      return;
    }
    setSubmitting(true);
    setSubmitError('');
    setSubmitSuccess(false);
    try {
      // Prepare payload
      const payload = {
        product: selectedSlot.product_id,
        session_date: selectedSlot.date,
        session_time: selectedSlot.time,
        notes: notes,
      };
      // Debug: log CSRF token
      console.log('CSRF token:', getCookie('csrftoken'));
      const res = await fetch('/api/bookings/book/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCookie('csrftoken'),
        },
        credentials: 'same-origin',
        body: JSON.stringify(payload),
      });
      if (res.ok) {
        setSubmitSuccess(true);
        setStep(1); // Optionally reset
        setNotes('');
        setSelectedSlot(null);
        setSelectedLength(null);
      } else {
        const data = await res.json();
        setSubmitError(data?.notes?.[0] || 'Booking failed.');
      }
    } catch (err) {
      setSubmitError('Booking failed. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  // Build week days (Mon-Sat)
  const weekDays = Array.from({ length: 6 }, (_, i) => addDays(weekStart, i));

  // Group slots by date for table display
  const slotsByDate = {};
  weekDays.forEach(day => {
    slotsByDate[formatDate(day)] = SLOT_HOURS.map(hour => {
      const slot = slots.find(s => s.date === formatDate(day) && s.time === `${hour.toString().padStart(2, '0')}:00`);
      return slot || { date: formatDate(day), time: `${hour.toString().padStart(2, '0')}:00`, reserved: false };
    });
  });

  // Format week range for display
  const weekRange = `${weekDays[0].toLocaleDateString(undefined, { day: 'numeric', month: 'short' })} - ${weekDays[5].toLocaleDateString(undefined, { day: 'numeric', month: 'short' })}`;

  return (
    <div className="container py-4">
      <h1>Book a Shiatsu Session</h1>
      <div className="accordion" id="bookingAccordion">
        {/* Step 1: Choose Length */}
        <div className="accordion-item">
          <h2 className="accordion-header" id="headingLength">
            <button
              className={`accordion-button ${step !== 1 ? 'collapsed' : ''}`}
              type="button"
              aria-expanded={step === 1}
              aria-controls="collapseLength"
              onClick={() => setStep(1)}
            >
              1. Choose Length
            </button>
          </h2>
          <div
            id="collapseLength"
            className={`accordion-collapse collapse ${step === 1 ? 'show' : ''}`}
            aria-labelledby="headingLength"
            data-bs-parent="#bookingAccordion"
          >
            <div className="accordion-body">
              <div className="d-flex gap-3">
                {SESSION_LENGTHS.map((length) => (
                  <button
                    key={length}
                    className={`btn btn-outline-primary ${selectedLength === length ? 'active' : ''}`}
                    onClick={() => handleLengthSelect(length)}
                  >
                    {length} minutes
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
        {/* Step 2: Choose Date & Time */}
        <div className="accordion-item">
          <h2 className="accordion-header" id="headingDateTime">
            <button
              className={`accordion-button ${step !== 2 ? 'collapsed' : ''}`}
              type="button"
              aria-expanded={step === 2}
              aria-controls="collapseDateTime"
              disabled={!selectedLength}
              onClick={() => selectedLength && setStep(2)}
            >
              2. Choose Date & Time
            </button>
          </h2>
          <div
            id="collapseDateTime"
            className={`accordion-collapse collapse ${step === 2 ? 'show' : ''}`}
            aria-labelledby="headingDateTime"
            data-bs-parent="#bookingAccordion"
          >
            <div className="accordion-body">
              {selectedLength && (
                <div>
                  <div className="d-flex align-items-center mb-3">
                    <button className="btn btn-outline-secondary btn-sm me-2" onClick={handlePrevWeek}>&lt;</button>
                    <span className="fw-bold">Change Week &nbsp; {weekRange}</span>
                    <button className="btn btn-outline-secondary btn-sm ms-2" onClick={handleNextWeek}>&gt;</button>
                  </div>
                  {loadingSlots ? (
                    <div className="text-info">Loading slots...</div>
                  ) : slotError ? (
                    <div className="text-danger">{slotError}</div>
                  ) : (
                    <div className="table-responsive">
                      <table className="table table-bordered text-center align-middle">
                        <thead>
                          <tr>
                            <th></th>
                            {weekDays.map((day, idx) => (
                              <th key={idx}>{WEEKDAYS[idx]}<br />{day.getDate()}/{day.getMonth()+1}</th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {SLOT_HOURS.map((hour, rowIdx) => (
                            <tr key={hour}>
                              <td className="fw-bold">{hour}:00</td>
                              {weekDays.map((day, colIdx) => {
                                const slot = slotsByDate[formatDate(day)][rowIdx];
                                const isSelected = selectedSlot && selectedSlot.date === slot.date && selectedSlot.time === slot.time;
                                return (
                                  <td key={colIdx}>
                                    <button
                                      className={`btn btn-sm rounded-pill ${
                                        slot.reserved
                                          ? 'btn-danger text-white'
                                          : 'btn-success text-white'
                                      }`}
                                      style={{ minWidth: 90, fontWeight: 500 }}
                                      disabled={slot.reserved}
                                      onClick={() => handleSlotSelect(slot)}
                                    >
                                      {slot.reserved ? 'Reserved' : isSelected ? 'Selected' : 'Available'}
                                    </button>
                                  </td>
                                );
                              })}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
        {/* Step 3: Add Notes */}
        <div className="accordion-item">
          <h2 className="accordion-header" id="headingNotes">
            <button
              className={`accordion-button ${step !== 3 ? 'collapsed' : ''}`}
              type="button"
              aria-expanded={step === 3}
              aria-controls="collapseNotes"
              disabled={!selectedSlot}
              onClick={() => selectedSlot && setStep(3)}
            >
              3. Add Notes
            </button>
          </h2>
          <div
            id="collapseNotes"
            className={`accordion-collapse collapse ${step === 3 ? 'show' : ''}`}
            aria-labelledby="headingNotes"
            data-bs-parent="#bookingAccordion"
          >
            <div className="accordion-body">
              {submitSuccess ? (
                <div className="alert alert-success">Booking successful!</div>
              ) : (
                <form onSubmit={handleBookingSubmit}>
                  <div className="mb-3">
                    <label htmlFor="notes" className="form-label">Notes (optional)</label>
                    <textarea
                      id="notes"
                      className={`form-control${notesError ? ' is-invalid' : ''}`}
                      rows={3}
                      maxLength={NOTES_MAX + 1}
                      value={notes}
                      onChange={e => setNotes(e.target.value)}
                      placeholder="Any notes or requests?"
                    />
                    <div className="d-flex justify-content-between small">
                      <div className="text-danger">{notesError}</div>
                      <div>{NOTES_MAX - notes.length} characters left</div>
                    </div>
                  </div>
                  {submitError && <div className="alert alert-danger">{submitError}</div>}
                  <button
                    type="submit"
                    className="btn btn-primary"
                    disabled={submitting || !!notesError || notes.length > NOTES_MAX}
                  >
                    {submitting ? 'Submitting...' : 'Make Booking'}
                  </button>
                </form>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default BookingsApp; 