// Include the token in HTMX calls
document.body.addEventListener('htmx:configRequest', (event) => {
    event.detail.headers['X-CSRFToken'] = '{{ csrf_token }}';
});

// Toggle comment section visibility
document.addEventListener('htmx:afterSwap', function(event) {
    if (event.target.classList.contains('comment-area') || event.target.closest('.comment-area')) {
        const commentArea = event.target.classList.contains('comment-area') ? event.target : event.target.closest('.comment-area');
        if (commentArea.style.display === 'none') {
            commentArea.style.display = 'block';
        }
    }
});