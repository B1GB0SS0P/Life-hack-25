// Restore saved preference
document.addEventListener('DOMContentLoaded', () => {
  chrome.storage.sync.get({ preferredMetric: 'carbonScore' }, prefs => {
    document.getElementById('metric-select').value = prefs.preferredMetric;
  });
});

// Save on click
document.getElementById('save-btn').onclick = () => {
  const val = document.getElementById('metric-select').value;
  chrome.storage.sync.set({ preferredMetric: val }, () => {
    alert('Preference saved!');
  });
};
