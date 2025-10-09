// Dashboard functionality

class Dashboard {
    constructor() {
        this.connectedAccounts = {
            instagram: false,
            twitter: false,
            linkedin: false,
            facebook: false
        };
        this.analysisData = null;
        
        this.init();
    }

    // Normalize a platform card's visual state
    setPlatformButtonState(platform, isConnected) {
        const button = document.querySelector(`[data-platform="${platform}"]`);
        const statusSpan = document.getElementById(`${platform}-status`);
        if (!button) return;

        // Remove any connected classes
        button.classList.remove('border-solid','border-green-500','bg-green-50','dark:bg-green-900/20');
        // Also ensure dashed/disconnected baseline is present
        button.classList.add('border-2','border-dashed','border-gray-300','dark:border-gray-600');

        if (isConnected) {
            // Switch to connected visual
            button.classList.remove('border-2','border-dashed','border-gray-300','dark:border-gray-600');
            button.classList.add('border-solid','border-green-500','bg-green-50','dark:bg-green-900/20');
            if (statusSpan) {
                statusSpan.textContent = 'Connected';
                statusSpan.className = 'text-xs text-green-600 dark:text-green-400 mt-1';
            }
        } else {
            if (statusSpan) {
                statusSpan.textContent = 'Not Connected';
                statusSpan.className = 'text-xs text-gray-500 dark:text-gray-400 mt-1';
            }
        }
    }
    
    init() {
        // Load user data from Django context
        this.loadUserData();
        this.bindEvents();
        // Restore last section from localStorage, default to 'home'
        const lastSection = localStorage.getItem('dashboardLastSection') || 'home';
        this.showSection(lastSection);
    }
    
    loadUserData() {
        // Get user data from Django template context
        const userEmail = document.getElementById('user-email');
        const userAvatar = document.getElementById('user-avatar');
        const userStatus = document.getElementById('user-status');
        const settingsEmail = document.getElementById('settings-email');
        
        if (userEmail) {
            const email = userEmail.getAttribute('data-user-email') || userEmail.textContent;
            if (settingsEmail) settingsEmail.value = email;
        }
        
        if (userAvatar) {
            const email = userEmail ? (userEmail.getAttribute('data-user-email') || userEmail.textContent) : '';
            const initials = email.substring(0, 2).toUpperCase();
            userAvatar.textContent = initials;
        }
        
        if (userStatus) {
            // Check if user is premium (you can add this logic based on Django user model)
            userStatus.textContent = 'Free Trial'; // Default status
        }
        
        // Load profile form data from Django context
        this.loadProfileData();
    }
    
    loadProfileData() {
        // Load profile data from Django template context
        const nameField = document.getElementById('user-name');
        const countryField = document.getElementById('user-country');
        const universityField = document.getElementById('user-university');
        
        // You can add data attributes to these fields in Django template
        if (nameField && nameField.getAttribute('data-value')) {
            nameField.value = nameField.getAttribute('data-value');
        }
        if (countryField && countryField.getAttribute('data-value')) {
            countryField.value = countryField.getAttribute('data-value');
        }
        if (universityField && universityField.getAttribute('data-value')) {
            universityField.value = universityField.getAttribute('data-value');
        }
    }
    
    loadConnectedAccounts() {
        // Load connected accounts from Django backend
        fetch('/dashboard/get-social-accounts/', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCSRFToken()
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Update connected accounts object
                this.connectedAccounts = {
                    instagram: !!data.accounts.instagram,
                    twitter: !!data.accounts.twitter,
                    linkedin: !!data.accounts.linkedin,
                    facebook: !!data.accounts.facebook
                };
                
                // Update UI for each platform consistently
                Object.keys(this.connectedAccounts).forEach(platform => {
                    const isConnected = !!this.connectedAccounts[platform];
                    this.setPlatformButtonState(platform, isConnected);
                });
                
                this.updateStartAnalysisButton();
            } else {
                console.error('Error loading social accounts:', data.message);
            }
        })
        .catch(error => {
            console.error('Error loading social accounts:', error);
            // Fallback to localStorage if backend fails
            this.loadConnectedAccountsFromStorage();
        });
    }
    
    loadConnectedAccountsFromStorage() {
        // Fallback method using localStorage
        const connectedAccounts = getStorageItem('connectedAccounts', {
            instagram: false,
            twitter: false,
            linkedin: false,
            facebook: false
        });
        
        this.connectedAccounts = connectedAccounts;
        
        // Update UI for each platform consistently
        Object.keys(this.connectedAccounts).forEach(platform => {
            const isConnected = (this.connectedAccounts[platform] === true || (this.connectedAccounts[platform] && this.connectedAccounts[platform].connected === true));
            this.setPlatformButtonState(platform, isConnected);
        });
        
        this.updateStartAnalysisButton();
    }
    
    updateStartAnalysisButton() {
        const startButton = document.getElementById('start-analysis-btn');
        if (!startButton) return;
        
        const connectedCount = Object.values(this.connectedAccounts).filter(account => {
            return account === true || (account && account.connected === true);
        }).length;
        
        if (connectedCount > 0) {
            startButton.disabled = false;
            startButton.classList.remove('opacity-50', 'cursor-not-allowed');
        } else {
            startButton.disabled = true;
            startButton.classList.add('opacity-50', 'cursor-not-allowed');
        }
    }
    
    bindEvents() {
        // Theme toggle
        const themeToggle = document.getElementById('theme-toggle-sidebar');
        if (themeToggle) {
            themeToggle.addEventListener('click', () => this.toggleTheme());
        }
        
        // Mobile sidebar
        this.initMobileSidebar();
        
        // Load connected accounts
        this.loadConnectedAccounts();

        // Add disconnect event listeners for social buttons
        ['instagram','facebook','twitter','linkedin'].forEach(platform => {
            const button = document.querySelector(`[data-platform="${platform}"]`);
            if (button) {
                // Add disconnect icon/button if not present
                let disconnectBtn = button.querySelector('.disconnect-btn');
                if (!disconnectBtn) {
                    disconnectBtn = document.createElement('button');
                    disconnectBtn.className = 'disconnect-btn ml-2 text-xs text-red-500 hover:text-red-700';
                    disconnectBtn.innerHTML = '<i class="fas fa-unlink"></i> Disconnect';
                    disconnectBtn.style.display = 'none';
                    button.appendChild(disconnectBtn);
                }
                // Show disconnect if connected
                const isConnected = this.connectedAccounts[platform] && (this.connectedAccounts[platform] === true || this.connectedAccounts[platform].connected === true);
                disconnectBtn.style.display = isConnected ? 'inline-block' : 'none';
                // Click handler
                disconnectBtn.onclick = (e) => {
                    e.stopPropagation();
                    fetch('/dashboard/disconnect-social-account/', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': this.getCSRFToken()
                        },
                        body: JSON.stringify({ platform })
                    })
                    .then(r => r.json())
                    .then(data => {
                        if (data.success) {
                            this.connectedAccounts[platform] = false;
                            // Normalize visual state
                            this.setPlatformButtonState(platform, false);
                            // Clear hidden input username
                            const hiddenInput = document.getElementById(`${platform}-username`);
                            if (hiddenInput) hiddenInput.value = '';
                            disconnectBtn.style.display = 'none';
                            this.updateStartAnalysisButton();
                            // Backend-sync fallback to ensure full UI consistency
                            this.loadConnectedAccounts();
                            showMessage(`${platform.charAt(0).toUpperCase()+platform.slice(1)} disconnected successfully!`, 'success');
                        } else {
                            showMessage('Failed to disconnect. ' + (data.error || ''), 'error');
                        }
                    })
                    .catch(() => showMessage('Error disconnecting account.', 'error'));
                };
            }
        });
    }

    showSection(sectionName) {
        // Persist last active section
        localStorage.setItem('dashboardLastSection', sectionName);
        // Hide all sections
        const sections = document.querySelectorAll('.section');
        sections.forEach(section => section.classList.add('hidden'));
        
        // Show selected section
        const targetSection = document.getElementById(`${sectionName}-section`);
        if (targetSection) {
            targetSection.classList.remove('hidden');
        }
        
        // Update navigation active state
        const navItems = document.querySelectorAll('.nav-item');
        navItems.forEach(item => item.classList.remove('active'));
        
        const activeNavItem = document.querySelector(`[onclick="showSection('${sectionName}')"]`);
        if (activeNavItem) {
            activeNavItem.classList.add('active');
        }
        
        // Update section title
        const sectionTitle = document.getElementById('section-title');
        if (sectionTitle) {
            const titles = {
                home: 'Dashboard',
                results: 'My Results'
            };
            sectionTitle.textContent = titles[sectionName] || 'Dashboard';
        }
        
        // Load section-specific data
        if (sectionName === 'results') {
            this.loadMyResults();
        }
    }
    
    connectAccount(platform) {
        this.showConnectionModal(platform);
    }
    
    showConnectionModal(platform) {
        const modal = document.getElementById('connection-modal');
        const modalTitle = document.getElementById('modal-title');
        const platformIcon = document.getElementById('modal-platform-icon');
        const usernameInput = document.getElementById('username-input');
        
        if (!modal || !modalTitle || !platformIcon || !usernameInput) return;
        
        const platformNames = {
            instagram: 'Instagram',
            twitter: 'X (Twitter)',
            linkedin: 'LinkedIn',
            facebook: 'Facebook'
        };
        
        const platformIcons = {
            instagram: 'fab fa-instagram text-pink-500',
            twitter: 'fab fa-x-twitter text-black dark:text-white',
            linkedin: 'fab fa-linkedin text-blue-600',
            facebook: 'fab fa-facebook text-blue-600'
        };
        
        modalTitle.textContent = `Connect to ${platformNames[platform]}`;
        platformIcon.className = platformIcons[platform];
        usernameInput.value = '';
        usernameInput.focus();
        
        modal.classList.remove('hidden');
        
        // Handle form submission
        const form = document.getElementById('connection-form');
        if (form) {
            form.onsubmit = (e) => {
                e.preventDefault();
                this.handleConnectionSubmit(platform);
            };
        }
    }
    
    handleConnectionSubmit(platform) {
        const usernameInput = document.getElementById('username-input');
        const saveBtn = document.getElementById('save-connection-btn');
        const saveBtnText = document.getElementById('save-btn-text');
        const saveBtnLoading = document.getElementById('save-btn-loading');
        
        if (!usernameInput || !saveBtn || !saveBtnText || !saveBtnLoading) return;
        
        const username = usernameInput.value.trim();
        if (!username) {
            showMessage('Please enter a username', 'error');
            return;
        }
        
        // Show loading state
        saveBtn.disabled = true;
        saveBtnText.classList.add('hidden');
        saveBtnLoading.classList.remove('hidden');
        
        // Send data to Django backend
        fetch('/dashboard/connect-social-account/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCSRFToken()
            },
            body: JSON.stringify({
                platform: platform,
                username: username
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                this.completeConnection(platform, username);
                // Update hidden input so other parts of the UI know it's connected immediately
                const hiddenInput = document.getElementById(`${platform}-username`);
                if (hiddenInput) hiddenInput.value = username;
                // Immediate DOM update for status text and classes (defensive in case of class mismatch)
                const statusSpan = document.getElementById(`${platform}-status`);
                if (statusSpan) {
                    statusSpan.textContent = 'Connected';
                    statusSpan.classList.remove('text-gray-500','dark:text-gray-400');
                    statusSpan.classList.add('text-green-600','dark:text-green-400');
                }
                const button = document.querySelector(`[data-platform="${platform}"]`);
                if (button) {
                    // Normalize classes to connected state
                    button.classList.remove('border-2','border-dashed','border-gray-300','dark:border-gray-600');
                    button.classList.add('border-solid','border-green-500','bg-green-50','dark:bg-green-900/20');
                }
                // Also re-fetch from backend to ensure absolute sync
                this.loadConnectedAccounts();
                showMessage(data.message, 'success');
            } else {
                showMessage(data.message || 'Error connecting account', 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showMessage('Error connecting account. Please try again.', 'error');
        })
        .finally(() => {
            // Reset button state
            saveBtn.disabled = false;
            saveBtnText.classList.remove('hidden');
            saveBtnLoading.classList.add('hidden');
            
            // Close modal
            this.closeConnectionModal();
        });
    }
    
    getCSRFToken() {
        // Get CSRF token from cookie
        const name = 'csrftoken';
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
    
    completeConnection(platform, username) {
        // Update connected accounts object
        this.connectedAccounts[platform] = true;
        
        // Update UI
        const button = document.querySelector(`[data-platform="${platform}"]`);
        if (button) {
            this.setPlatformButtonState(platform, true);
            const statusSpan = document.getElementById(`${platform}-status`);
            if (statusSpan) {
                statusSpan.textContent = 'Connected';
                statusSpan.className = 'text-xs text-green-600 dark:text-green-400 mt-1';
            }
        }
        
        this.updateStartAnalysisButton();
    }
    
    closeConnectionModal() {
        const modal = document.getElementById('connection-modal');
        if (modal) {
            modal.classList.add('hidden');
        }
    }
    
    startAnalysis() {
        const connectedCount = Object.values(this.connectedAccounts).filter(account => {
            return account === true || (account && account.connected === true);
        }).length;
        
        if (connectedCount === 0) {
            showMessage('Please connect at least one social media account to start analysis', 'warning');
            return;
        }

        // If payment_success is present in URL, fully redirect to dashboard (removes all params/results)
        const url = new URL(window.location);
        if (url.searchParams.has('payment_success')) {
            window.location.href = '/dashboard/';
            return;
        }

        // Clear payment_success parameter from URL to reset payment status for new analysis
        if (url.searchParams.has('payment_success')) {
            url.searchParams.delete('payment_success');
            window.history.replaceState({}, document.title, url.toString());
        }

        // AJAX call to reset payment_completed before analysis
        fetch('/dashboard/reset-payment-status/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCSRFToken()
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                this.showLoadingModal();
                this.runRealAnalysis(); // Changed from runAnalysisSimulation to runRealAnalysis
            } else {
                showMessage('Could not reset payment status. Please try again.', 'error');
            }
        })
        .catch(err => {
            showMessage('Error contacting server. Please try again.', 'error');
        });
    }
    
    runRealAnalysis() {
        // Start real analysis by calling backend
        fetch('/dashboard/start-analysis/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCSRFToken()
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                console.log('✅ Analysis started successfully');
                // Poll for progress
                this.pollAnalysisProgress();
            } else {
                this.hideLoadingModal();
                showMessage(data.error || 'Failed to start analysis', 'error');
            }
        })
        .catch(err => {
            console.error('❌ Error starting analysis:', err);
            this.hideLoadingModal();
            showMessage('Error starting analysis. Please try again.', 'error');
        });
    }

    pollAnalysisProgress() {
        const progressBar = document.getElementById('progress-bar');
        const loadingMessage = document.getElementById('loading-message');
        
        const checkProgress = () => {
            fetch('/dashboard/analysis-progress/', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                }
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                console.log('Progress:', data);
                
                // Cap progress at 100%
                const progress = Math.min(data.progress || 0, 100);
                
                if (loadingMessage) {
                    loadingMessage.textContent = data.message || 'Processing...';
                }
                if (progressBar) {
                    progressBar.style.width = progress + '%';
                }
                
                // Check for error status
                if (data.status === 'error') {
                    console.error('❌ Analysis error:', data.message);
                    this.hideLoadingModal();
                    showMessage(data.message || 'Analysis failed. Please try again.', 'error');
                    return; // Stop polling
                }
                
                if (data.status === 'complete') {
                    // Analysis complete
                    console.log('✅ Analysis complete!');
                    this.hideLoadingModal();
                    // Reload page to show results
                    window.location.href = '/dashboard/?analysis_complete=1';
                } else {
                    // Continue polling
                    setTimeout(checkProgress, 2000); // Check every 2 seconds
                }
            })
            .catch(err => {
                console.error('❌ Error checking progress:', err);
                this.hideLoadingModal();
                showMessage('Error checking analysis progress. Please try again.', 'error');
            });
        };
        
        checkProgress();
    }

    showLoadingModal() {
        const modal = document.getElementById('loading-overlay');
        if (modal) {
            modal.classList.remove('hidden');
        }
    }
    
    hideLoadingModal() {
        const modal = document.getElementById('loading-overlay');
        if (modal) {
            modal.classList.add('hidden');
        }
    }
    
    showInstagramPostsSection() {
        const postsSection = document.getElementById('instagram-posts-section');
        if (postsSection) postsSection.classList.remove('hidden');
    }
    showInstagramCommentsSection() {
        const commentsSection = document.getElementById('instagram-comments-section');
        if (commentsSection) commentsSection.classList.remove('hidden');
    }
    showDigitalFootprintSection() {
        const footprintSection = document.getElementById('digital-footprint-section');
        if (footprintSection) footprintSection.classList.remove('hidden');
    }

    runAnalysisSimulation() {
        const progressBar = document.getElementById('progress-bar');
        const loadingMessage = document.getElementById('loading-message');
        const analysisResults = document.getElementById('analysis-results');
        // Hide all result sections initially
        if (analysisResults) analysisResults.classList.add('hidden');

        // Steps for sequential analysis
        const steps = [
            {
                label: 'Analyzing Instagram posts...',
                progress: 33,
                show: () => {
                    // Show only Instagram posts section
                    this.showInstagramPostsSection && this.showInstagramPostsSection();
                }
            },
            {
                label: 'Analyzing Instagram comments...',
                progress: 66,
                show: () => {
                    this.showInstagramCommentsSection && this.showInstagramCommentsSection();
                }
            },
            {
                label: 'Analyzing digital footprint...',
                progress: 100,
                show: () => {
                    this.showDigitalFootprintSection && this.showDigitalFootprintSection();
                }
            }
        ];

        let currentStep = 0;
        function nextStep() {
            if (currentStep < steps.length) {
                if (loadingMessage) loadingMessage.textContent = steps[currentStep].label;
                if (progressBar) progressBar.style.width = steps[currentStep].progress + '%';
                if (typeof steps[currentStep].show === 'function') steps[currentStep].show();
                currentStep++;
                setTimeout(nextStep, 1800); // Wait before next step
            } else {
                setTimeout(() => {
                    if (progressBar) progressBar.style.width = '100%';
                    this.hideLoadingModal();
                    if (analysisResults) analysisResults.classList.remove('hidden');
                    this.showAnalysisResults();
                }, 800);
            }
        }
        nextStep = nextStep.bind(this);
        nextStep();
    }
    
    showAnalysisResults() {
        // Generate analysis data
        this.generateAnalysisData();
        
        // Show results section
        const resultsDiv = document.getElementById('analysis-results');
        if (resultsDiv) {
            resultsDiv.classList.remove('hidden');
        }
        
        // Always show locked preview after new analysis
        this.showFreeTrialResults();
        
        // Save analysis data
        this.saveAnalysisData();
        
        showMessage('Analysis completed! View your results below.', 'success');
    }
    
    saveAnalysisData() {
        if (this.analysisData) {
            setStorageItem('lastAnalysis', {
                ...this.analysisData,
                timestamp: new Date().toISOString()
            });
        }
    }
    
    generateAnalysisData() {
        this.analysisData = {
            overallRisk: 'low',
            approvalChance: 92,
            postsAnalyzed: 847,
            flaggedItems: 3,
            platforms: ['instagram', 'linkedin', 'twitter'],
            platformAnalysis: {
                instagram: { risk: 'low', score: 85 },
                linkedin: { risk: 'moderate', score: 65 },
                twitter: { risk: 'high', score: 35 }
            },
            flaggedContent: [
                {
                    platform: 'instagram',
                    content: 'Beautiful sunset at Stanford campus! 🌅',
                    risk: 'low',
                    tags: ['#Stanford', '#StudentLife']
                },
                {
                    platform: 'tiktok',
                    content: 'Party with friends last weekend! 🎉',
                    risk: 'moderate',
                    tags: ['#Party', '#Weekend']
                }
            ],
            recommendations: [
                {
                    type: 'high',
                    title: 'Remove political content',
                    description: 'Delete posts containing political opinions or activism references',
                    affectedPosts: 2
                },
                {
                    type: 'medium',
                    title: 'Add context to social posts',
                    description: 'Provide background information for party or social gathering posts',
                    affectedPosts: 3
                }
            ]
        };
    }
    
    showFreeTrialResults() {
        // Hide full results, show preview results
        const previewResults = document.getElementById('preview-results');
        const fullResults = document.getElementById('full-results');
        if (previewResults) previewResults.classList.remove('hidden');
        if (fullResults) fullResults.classList.add('hidden');
    }
    
    // showFullResults() {
    //     const freeTrialResults = document.getElementById('free-trial-results');
    //     const fullResults = document.getElementById('full-results');
        
    //     if (freeTrialResults) freeTrialResults.classList.add('hidden');
    //     if (fullResults) fullResults.classList.remove('hidden');
        
    //     this.populateFullResults();
    // }
    
    populateFullResults() {
        if (!this.analysisData) return;
        
        // Update risk score
        const riskScore = document.getElementById('risk-score');
        const riskCircle = document.getElementById('risk-circle');
        
        if (riskScore) {
            const score = this.analysisData.approvalChance;
            riskScore.textContent = `${100 - score}%`;
        }
        
        if (riskCircle) {
            const score = this.analysisData.approvalChance;
            const circumference = 2 * Math.PI * 40;
            const offset = circumference - (score / 100) * circumference;
            riskCircle.style.strokeDashoffset = offset;
        }
        
        // Populate platform analysis
        this.populatePlatformAnalysis();
        
        // Populate risk categories
        this.populateRiskCategories();
        
        // Populate flagged content
        this.populateFlaggedContent();
    }
    
    populatePlatformAnalysis() {
        const container = document.getElementById('platform-analysis');
        if (!container || !this.analysisData) return;
        
        container.innerHTML = '';
        
        Object.entries(this.analysisData.platformAnalysis).forEach(([platform, data]) => {
            const platformDiv = document.createElement('div');
            platformDiv.className = 'flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700 rounded-lg';
            
            const riskColor = getRiskColor(data.risk);
            const riskText = getRiskText(data.risk);
            const platformIcon = getPlatformIcon(platform);
            
            platformDiv.innerHTML = `
                <div class="flex items-center space-x-3">
                    <i class="${platformIcon} text-2xl"></i>
                    <span class="font-medium text-gray-900 dark:text-white">${platform.charAt(0).toUpperCase() + platform.slice(1)}</span>
                </div>
                <div class="flex items-center space-x-3">
                    <div class="w-24 bg-gray-200 dark:bg-gray-600 rounded-full h-2">
                        <div class="bg-${data.risk === 'low' ? 'green' : data.risk === 'moderate' ? 'yellow' : 'red'}-500 h-2 rounded-full" style="width: ${data.score}%"></div>
                    </div>
                    <span class="text-sm ${riskColor} font-medium">${riskText}</span>
                </div>
            `;
            
            container.appendChild(platformDiv);
        });
    }
    
    populateRiskCategories() {
        const container = document.getElementById('risk-categories');
        if (!container || !this.analysisData) return;
        
        container.innerHTML = '';
        
        const categories = [
            { name: 'Political Content', risk: 'high', count: 2 },
            { name: 'Social Activities', risk: 'moderate', count: 3 },
            { name: 'Educational Content', risk: 'low', count: 15 }
        ];
        
        categories.forEach(category => {
            const categoryDiv = document.createElement('div');
            categoryDiv.className = 'p-4 border rounded-lg';
            
            const riskColor = getRiskColor(category.risk);
            const riskText = getRiskText(category.risk);
            
            categoryDiv.innerHTML = `
                <h4 class="font-medium text-gray-900 dark:text-white mb-2">${category.name}</h4>
                <div class="flex items-center justify-between">
                    <span class="text-sm ${riskColor} font-medium">${riskText}</span>
                    <span class="text-sm text-gray-500 dark:text-gray-400">${category.count} posts</span>
                </div>
            `;
            
            container.appendChild(categoryDiv);
        });
    }
    
    populateFlaggedContent() {
        const container = document.getElementById('flagged-content');
        if (!container || !this.analysisData) return;
        
        container.innerHTML = '';
        
        this.analysisData.flaggedContent.forEach(content => {
            const contentDiv = document.createElement('div');
            contentDiv.className = 'p-4 border rounded-lg mb-4';
            
            const riskColor = getRiskColor(content.risk);
            const riskText = getRiskText(content.risk);
            const platformIcon = getPlatformIcon(content.platform);
            
            contentDiv.innerHTML = `
                <div class="flex items-start justify-between mb-3">
                    <div class="flex items-center space-x-2">
                        <i class="${platformIcon}"></i>
                        <span class="text-xs bg-gray-200 text-gray-800 px-2 py-1 rounded-full font-medium">${content.platform.charAt(0).toUpperCase() + content.platform.slice(1)}</span>
                    </div>
                    <div class="text-xs ${riskColor} font-medium">${riskText}</div>
                </div>
                <h5 class="font-medium text-gray-900 dark:text-white mb-2">${content.content}</h5>
                <p class="text-xs text-gray-600 dark:text-gray-400 mb-2">${content.tags.join(' ')}</p>
                <p class="text-sm text-gray-700 dark:text-gray-300">Content flagged for review</p>
            `;
            
            container.appendChild(contentDiv);
        });
    }
    
    getPlatformIcon(platform) {
        return getPlatformIcon(platform);
    }
    
    getPlatformColor(platform) {
        const colors = {
            instagram: 'pink',
            facebook: 'blue',
            twitter: 'black',
            linkedin: 'blue'
        };
        return colors[platform] || 'gray';
    }
    
    loadMyResults() {
        // Load saved analysis data
        const savedAnalysis = getStorageItem('lastAnalysis');
        if (savedAnalysis) {
            this.analysisData = savedAnalysis;
            this.updateResultsDisplay();
        } else {
            // Show no results message
            const noResultsMessage = document.getElementById('no-results-message');
            const resultsDisplay = document.getElementById('results-display');
            
            if (noResultsMessage) noResultsMessage.classList.remove('hidden');
            if (resultsDisplay) resultsDisplay.classList.add('hidden');
        }
    }
    
    updateResultsDisplay() {
        if (!this.analysisData) return;
        
        // Show results display
        const noResultsMessage = document.getElementById('no-results-message');
        const resultsDisplay = document.getElementById('results-display');
        
        if (noResultsMessage) noResultsMessage.classList.add('hidden');
        if (resultsDisplay) resultsDisplay.classList.remove('hidden');
        
        // Update metrics
        this.updateResultsMetrics();
        
        // Update platform results
        this.updatePlatformResults();
        
        // Update flagged content
        this.updateFlaggedContentResults();
        
        // Update recommendations
        this.updateRecommendations();
        
        // Load results history
        this.loadResultsHistory();
    }
    
    updateResultsMetrics() {
        if (!this.analysisData) return;
        
        const overallRiskDisplay = document.getElementById('overall-risk-display');
        const approvalChanceDisplay = document.getElementById('approval-chance-display');
        const postsAnalyzedDisplay = document.getElementById('posts-analyzed-display');
        const flaggedItemsDisplay = document.getElementById('flagged-items-display');
        const analysisDate = document.getElementById('analysis-date');
        
        if (overallRiskDisplay) {
            overallRiskDisplay.textContent = this.analysisData.overallRisk.charAt(0).toUpperCase() + this.analysisData.overallRisk.slice(1);
        }
        
        if (approvalChanceDisplay) {
            approvalChanceDisplay.textContent = `${this.analysisData.approvalChance}%`;
        }
        
        if (postsAnalyzedDisplay) {
            postsAnalyzedDisplay.textContent = this.analysisData.postsAnalyzed;
        }
        
        if (flaggedItemsDisplay) {
            flaggedItemsDisplay.textContent = this.analysisData.flaggedItems;
        }
        
        if (analysisDate && this.analysisData.timestamp) {
            analysisDate.textContent = formatDate(this.analysisData.timestamp);
        }
    }
    
    updatePlatformResults() {
        const container = document.getElementById('platform-results');
        if (!container || !this.analysisData) return;
        
        container.innerHTML = '';
        
        Object.entries(this.analysisData.platformAnalysis).forEach(([platform, data]) => {
            const platformDiv = document.createElement('div');
            platformDiv.className = 'flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-lg';
            
            const riskColor = getRiskColor(data.risk);
            const riskText = getRiskText(data.risk);
            const platformIcon = getPlatformIcon(platform);
            
            platformDiv.innerHTML = `
                <div class="flex items-center space-x-3">
                    <i class="${platformIcon}"></i>
                    <span class="text-gray-900 dark:text-white">${platform.charAt(0).toUpperCase() + platform.slice(1)}</span>
                </div>
                <div class="flex items-center space-x-3">
                    <div class="w-24 bg-gray-200 dark:bg-gray-600 rounded-full h-2">
                        <div class="bg-${data.risk === 'low' ? 'green' : data.risk === 'moderate' ? 'yellow' : 'red'}-500 h-2 rounded-full" style="width: ${data.score}%"></div>
                    </div>
                    <span class="text-sm ${riskColor} font-medium">${riskText}</span>
                </div>
            `;
            
            container.appendChild(platformDiv);
        });
    }
    
    updateFlaggedContentResults() {
        const container = document.getElementById('flagged-content-results');
        if (!container || !this.analysisData) return;
        
        container.innerHTML = '';
        
        this.analysisData.flaggedContent.forEach(content => {
            const contentDiv = document.createElement('div');
            contentDiv.className = 'p-4 border rounded-lg mb-3';
            
            const riskColor = getRiskColor(content.risk);
            const riskText = getRiskText(content.risk);
            const platformIcon = getPlatformIcon(content.platform);
            
            contentDiv.innerHTML = `
                <div class="flex items-start justify-between mb-2">
                    <div class="flex items-center space-x-2">
                        <i class="${platformIcon}"></i>
                        <span class="text-xs bg-gray-200 text-gray-800 px-2 py-1 rounded-full">${content.platform.charAt(0).toUpperCase() + content.platform.slice(1)}</span>
                    </div>
                    <span class="text-xs ${riskColor} font-medium">${riskText}</span>
                </div>
                <p class="text-sm text-gray-900 dark:text-white mb-1">${content.content}</p>
                <p class="text-xs text-gray-600 dark:text-gray-400">${content.tags.join(' ')}</p>
            `;
            
            container.appendChild(contentDiv);
        });
    }
    
    updateRecommendations() {
        const container = document.getElementById('recommendations-results');
        if (!container || !this.analysisData) return;
        
        container.innerHTML = '';
        
        this.analysisData.recommendations.forEach(rec => {
            const recDiv = document.createElement('div');
            recDiv.className = 'p-4 border rounded-lg mb-3';
            
            const typeColor = rec.type === 'high' ? 'red' : rec.type === 'medium' ? 'yellow' : 'green';
            const typeIcon = rec.type === 'high' ? 'exclamation-circle' : rec.type === 'medium' ? 'exclamation-triangle' : 'check-circle';
            
            recDiv.innerHTML = `
                <div class="flex items-start space-x-3">
                    <div class="flex-shrink-0">
                        <i class="fas fa-${typeIcon} text-${typeColor}-600 mt-1"></i>
                    </div>
                    <div class="flex-1">
                        <h5 class="font-medium text-${typeColor}-900 dark:text-${typeColor}-100 mb-2">${rec.title}</h5>
                        <p class="text-sm text-${typeColor}-700 dark:text-${typeColor}-300 mb-2">${rec.description}</p>
                        <div class="flex items-center text-xs text-${typeColor}-600 dark:text-${typeColor}-400">
                            <i class="fas fa-file-alt mr-1"></i>
                            <span>Affects ${rec.affectedPosts} posts</span>
                        </div>
                    </div>
                </div>
            `;
            
            container.appendChild(recDiv);
        });
    }
    
    loadResultsHistory() {
        const container = document.getElementById('results-history');
        if (!container) return;
        
        // Load history from localStorage
        const history = getStorageItem('analysisHistory', []);
        
        if (history.length === 0) {
            container.innerHTML = `
                <div class="text-center py-8 text-gray-500 dark:text-gray-400">
                    <i class="fas fa-history text-3xl mb-3"></i>
                    <p>No analysis history yet</p>
                </div>
            `;
            return;
        }
        
        container.innerHTML = '';
        
        history.forEach(item => {
            const historyDiv = document.createElement('div');
            historyDiv.className = 'flex items-center justify-between p-4 border rounded-lg mb-3';
            
            historyDiv.innerHTML = `
                <div class="flex items-center space-x-3">
                    <div class="w-10 h-10 bg-primary-100 dark:bg-primary-900 rounded-full flex items-center justify-center">
                        <i class="fas fa-chart-line text-primary-600"></i>
                    </div>
                    <div>
                        <h4 class="font-medium text-gray-900 dark:text-white">Analysis #${item.id}</h4>
                        <p class="text-sm text-gray-500 dark:text-gray-400">${formatDate(item.timestamp)}</p>
                    </div>
                </div>
                <div class="text-right">
                    <div class="text-sm font-medium text-gray-900 dark:text-white">${item.overallRisk.charAt(0).toUpperCase() + item.overallRisk.slice(1)} Risk</div>
                    <div class="text-xs text-gray-500 dark:text-gray-400">${item.postsAnalyzed} posts analyzed</div>
                </div>
            `;
            
            container.appendChild(historyDiv);
        });
    }
    
    changePassword() {
        showMessage('Password change functionality will be handled by Django backend', 'info');
    }
    
    downloadData() {
        showMessage('Data download functionality will be handled by Django backend', 'info');
    }
    
    deleteAccount() {
        showMessage('Account deletion functionality will be handled by Django backend', 'info');
    }
    
    downloadReport() {
        if (!this.analysisData) {
            showMessage('No analysis data available to download', 'warning');
            return;
        }
        
        // Create a simple text report
        const report = this.generateTextReport();
        
        // Create download link
        const blob = new Blob([report], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `visaguard-analysis-${new Date().toISOString().split('T')[0]}.txt`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        showMessage('Report downloaded successfully!', 'success');
    }
    
    generateTextReport() {
        if (!this.analysisData) return 'No analysis data available.';
        
        let report = 'VisaGuardAI Analysis Report\n';
        report += '==========================\n\n';
        report += `Analysis Date: ${formatDate(this.analysisData.timestamp)}\n`;
        report += `Overall Risk: ${this.analysisData.overallRisk.toUpperCase()}\n`;
        report += `Approval Chance: ${this.analysisData.approvalChance}%\n`;
        report += `Posts Analyzed: ${this.analysisData.postsAnalyzed}\n`;
        report += `Flagged Items: ${this.analysisData.flaggedItems}\n\n`;
        
        report += 'Platform Analysis:\n';
        Object.entries(this.analysisData.platformAnalysis).forEach(([platform, data]) => {
            report += `- ${platform.charAt(0).toUpperCase() + platform.slice(1)}: ${data.risk.toUpperCase()} risk (${data.score}% score)\n`;
        });
        
        report += '\nFlagged Content:\n';
        this.analysisData.flaggedContent.forEach((content, index) => {
            report += `${index + 1}. ${content.platform.toUpperCase()}: ${content.content}\n`;
            report += `   Risk: ${content.risk.toUpperCase()}\n`;
        });
        
        report += '\nRecommendations:\n';
        this.analysisData.recommendations.forEach((rec, index) => {
            report += `${index + 1}. ${rec.title}\n`;
            report += `   ${rec.description}\n`;
            report += `   Affects ${rec.affectedPosts} posts\n\n`;
        });
        
        return report;
    }
    
    toggleTheme() {
        const html = document.documentElement;
        const isDark = html.classList.contains('dark');
        
        if (isDark) {
            html.classList.remove('dark');
            localStorage.setItem('theme', 'light');
        } else {
            html.classList.add('dark');
            localStorage.setItem('theme', 'dark');
        }
    }
    
    initMobileSidebar() {
        const sidebar = document.getElementById('sidebar');
        const mobileToggle = document.getElementById('mobile-sidebar-toggle');
        const mobileClose = document.getElementById('mobile-sidebar-close');
        const overlay = document.createElement('div');
        
        // Create overlay
        overlay.className = 'fixed inset-0 bg-black bg-opacity-50 z-30 hidden md:hidden';
        overlay.id = 'sidebar-overlay';
        document.body.appendChild(overlay);
        
        function showSidebar() {
            sidebar.classList.remove('-translate-x-full');
            overlay.classList.remove('hidden');
            document.body.classList.add('overflow-hidden');
        }
        
        function hideSidebar() {
            sidebar.classList.add('-translate-x-full');
            overlay.classList.add('hidden');
            document.body.classList.remove('overflow-hidden');
        }
        
        // Event listeners
        if (mobileToggle) {
            mobileToggle.addEventListener('click', showSidebar);
        }
        
        if (mobileClose) {
            mobileClose.addEventListener('click', hideSidebar);
        }
        
        overlay.addEventListener('click', hideSidebar);
        
        // Close sidebar when clicking on navigation items on mobile
        const navItems = sidebar.querySelectorAll('button[onclick]');
        navItems.forEach(item => {
            item.addEventListener('click', () => {
                if (window.innerWidth < 768) {
                    hideSidebar();
                }
            });
        });
    }
}

// Global functions for onclick handlers
function showSection(sectionName) {
    if (window.dashboard) {
        window.dashboard.showSection(sectionName);
    }
}

function connectAccount(platform) {
    if (window.dashboard) {
        window.dashboard.connectAccount(platform);
    }
}

function startAnalysis() {
    if (window.dashboard) {
        window.dashboard.startAnalysis();
    }
}

function changePassword() {
    if (window.dashboard) {
        window.dashboard.changePassword();
    }
}

function downloadData() {
    if (window.dashboard) {
        window.dashboard.downloadData();
    }
}

function deleteAccount() {
    if (window.dashboard) {
        window.dashboard.deleteAccount();
    }
}

function downloadReport() {
    if (window.dashboard) {
        window.dashboard.downloadReport();
    }
}

function closeConnectionModal() {
    if (window.dashboard) {
        window.dashboard.closeConnectionModal();
    }
}

// Mobile sidebar functionality
function initMobileSidebar() {
    const sidebar = document.getElementById('sidebar');
    const mobileToggle = document.getElementById('mobile-sidebar-toggle');
    const mobileClose = document.getElementById('mobile-sidebar-close');
    const overlay = document.createElement('div');
    
    // Create overlay
    overlay.className = 'fixed inset-0 bg-black bg-opacity-50 z-30 hidden md:hidden';
    overlay.id = 'sidebar-overlay';
    document.body.appendChild(overlay);
    
    function showSidebar() {
        sidebar.classList.remove('-translate-x-full');
        overlay.classList.remove('hidden');
        document.body.classList.add('overflow-hidden');
    }
    
    function hideSidebar() {
        sidebar.classList.add('-translate-x-full');
        overlay.classList.add('hidden');
        document.body.classList.remove('overflow-hidden');
    }
    
    // Event listeners
    if (mobileToggle) {
        mobileToggle.addEventListener('click', showSidebar);
    }
    
    if (mobileClose) {
        mobileClose.addEventListener('click', hideSidebar);
    }
    
    overlay.addEventListener('click', hideSidebar);
    
    // Close sidebar when clicking on navigation items on mobile
    const navItems = sidebar.querySelectorAll('button[onclick]');
    navItems.forEach(item => {
        item.addEventListener('click', () => {
            if (window.innerWidth < 768) {
                hideSidebar();
            }
        });
    });
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new Dashboard();
    initMobileSidebar();
});
