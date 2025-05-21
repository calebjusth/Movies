
document.addEventListener('DOMContentLoaded', function() {
    // Get both search inputs and results containers
    const desktopSearchInput = document.getElementById('SearchInput');
    const mobileSearchInput = document.getElementById('searchInput');
    const desktopSearchResults = document.getElementById('SearchResults');
    const mobileSearchResults = document.getElementById('SearchResults');
    
    let searchTimeout;
    
    // Debounce function to limit API calls
    function debounce(func, delay) {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(func, delay);
    }
    
    // Fetch search results
    function fetchSearchResults(query, resultsContainer) {
        if (query.length < 2) {
            resultsContainer.style.display = 'none';
            return;
        }
        
        fetch(`/search/?query=${encodeURIComponent(query)}`)
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    console.error('Search error:', data.error);
                    return;
                }
                
                displayResults(data.results, resultsContainer);
            })
            .catch(error => {
                console.error('Search failed:', error);
            });
    }
    
    // Display results in dropdown
    function displayResults(results, container) {
        container.innerHTML = '';
        
        if (results.length === 0) {
            container.innerHTML = '<div class="no-results">No results found</div>';
            container.style.display = 'block';
            return;
        }
        
        results.forEach(item => {
            const resultItem = document.createElement('div');
            resultItem.className = 'search-result-item';
            
            const posterPath = item.poster_path 
                ? `https://image.tmdb.org/t/p/w92${item.poster_path}`
                : '/static/images/no-poster.png';
            
            const mediaTypeIcon = item.media_type === 'movie' 
                ? '<i class="fas fa-film"></i>' 
                : '<i class="fas fa-tv"></i>';
            
            resultItem.innerHTML = `
                <img src="${posterPath}" alt="${item.title}" onerror="this.src='/static/images/no-poster.png'">
                <div class="search-result-info">
                    <h4>${item.title}</h4>
                    <div class="search-meta">
                        <span class="media-type">${mediaTypeIcon} ${item.media_type === 'movie' ? 'Movie' : 'TV Show'}</span>
                        ${item.year ? `<span class="year">• ${item.year}</span>` : ''}
                    </div>
                    <p class="search-overview">${item.overview}</p>
                </div>
            `;
            
            resultItem.addEventListener('click', () => {
                if (item.media_type === 'movie') {
                    window.location.href = `/watch/movie/${item.id}/`;
                } else {
                    window.location.href = `/watch/tv/${item.id}/`;
                }
            });
            
            container.appendChild(resultItem);
        });
        
        container.style.display = 'block';
    }
    
    // Setup event listeners for desktop search
    if (desktopSearchInput && desktopSearchResults) {
        desktopSearchInput.addEventListener('input', () => {
            const query = desktopSearchInput.value.trim();
            debounce(() => fetchSearchResults(query, desktopSearchResults), 300);
        });
        
        // Hide results when clicking outside (desktop)
        document.addEventListener('click', (e) => {
            if (!desktopSearchInput.contains(e.target) && !desktopSearchResults.contains(e.target)) {
                desktopSearchResults.style.display = 'none';
            }
        });
        
        // Keyboard navigation (desktop)
        desktopSearchInput.addEventListener('keydown', (e) => {
            handleSearchKeydown(e, desktopSearchInput, desktopSearchResults);
        });
    }
    
    // Setup event listeners for mobile search
    if (mobileSearchInput && mobileSearchResults) {
        mobileSearchInput.addEventListener('input', () => {
            const query = mobileSearchInput.value.trim();
            debounce(() => fetchSearchResults(query, mobileSearchResults), 300);
        });
        
        // Hide results when clicking outside (mobile)
        document.addEventListener('click', (e) => {
            if (!mobileSearchInput.contains(e.target) && !mobileSearchResults.contains(e.target)) {
                mobileSearchResults.style.display = 'none';
            }
        });
        
        // Keyboard navigation (mobile)
        mobileSearchInput.addEventListener('keydown', (e) => {
            handleSearchKeydown(e, mobileSearchInput, mobileSearchResults);
        });
    }
    
    // Shared keyboard navigation function
    function handleSearchKeydown(e, inputElement, resultsContainer) {
        if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
            const items = resultsContainer.querySelectorAll('.search-result-item');
            if (items.length === 0) return;
            
            let currentIndex = -1;
            items.forEach((item, index) => {
                if (item.classList.contains('highlighted')) {
                    currentIndex = index;
                    item.classList.remove('highlighted');
                }
            });
            
            if (e.key === 'ArrowDown') {
                currentIndex = (currentIndex + 1) % items.length;
            } else {
                currentIndex = (currentIndex - 1 + items.length) % items.length;
            }
            
            items[currentIndex].classList.add('highlighted');
            items[currentIndex].scrollIntoView({ block: 'nearest' });
            
            if (e.key === 'Enter' && currentIndex >= 0) {
                items[currentIndex].click();
            }
            
            e.preventDefault();
        } else if (e.key === 'Enter') {
            const highlighted = resultsContainer.querySelector('.highlighted');
            if (highlighted) {
                highlighted.click();
            }
        }
    }
});