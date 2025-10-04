document.addEventListener('DOMContentLoaded', function () {
    // Only start Twitter analysis after Instagram and LinkedIn are loaded
    function showTwitterLoader() {
        const twLoader = document.getElementById('twitter-loading');
        if (twLoader) twLoader.style.display = 'block';
    }
    function hideTwitterLoader() {
        const twLoader = document.getElementById('twitter-loading');
        if (twLoader) twLoader.style.display = 'none';
    }
    function renderTwitterAnalysis(data) {
        const twResult = document.getElementById('twitter-analysis-result');
        if (twResult) {
            if (data.success && data.twitter_analysis) {
                twResult.textContent = JSON.stringify(data.twitter_analysis, null, 2);
            } else {
                twResult.textContent = 'Error: ' + (data.error || 'Unknown error');
            }
        }
    }
    // Wait for Instagram and LinkedIn to finish (simulate with DOM ready)
    setTimeout(function () {
        showTwitterLoader();
        fetch('/dashboard/twitter_analysis_ajax/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': window.CSRF_TOKEN,
                'Content-Type': 'application/json',
            },
            credentials: 'same-origin',
        })
            .then(response => response.json())
            .then(data => {
                hideTwitterLoader();
                renderTwitterAnalysis(data);
            })
            .catch(err => {
                hideTwitterLoader();
                renderTwitterAnalysis({success: false, error: err.toString()});
            });
    }, 1000); // Simulate delay after other analyses
});
