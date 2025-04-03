/**
 * expert-roles.js - Part of Reflexia Model Manager
 * 
 * Copyright (c) 2025 Matthew D. Scott
 * All rights reserved.
 * 
 * This source code is licensed under the Reflexia Model Manager License
 * found in the LICENSE file in the root directory of this source tree.
 * 
 * Unauthorized use, reproduction, or distribution is prohibited.
 */

// Expert Roles Integration
document.addEventListener('DOMContentLoaded', function() {
    // Expert roles container
    const rolesContainer = document.getElementById('expert-roles');
    const systemPrompt = document.getElementById('system-prompt');
    let activeRoleBtn = null;
    
    // Expert roles by domain
    const expertRoles = {
        "Technology": [
            { id: "software_engineer", name: "Software Engineer", icon: "👨‍💻", system: "You are an expert software engineer with extensive experience across multiple programming languages and software architectures." },
            { id: "data_scientist", name: "Data Scientist", icon: "📊", system: "You are an expert data scientist skilled in statistical analysis, machine learning, and data visualization." },
            { id: "cybersecurity", name: "Cybersecurity", icon: "🔒", system: "You are a cybersecurity expert with deep knowledge of threat detection, security architecture, and ethical hacking." }
        ],
        "Business": [
            { id: "management", name: "Management", icon: "📈", system: "You are a management consultant with expertise in organizational theory, strategic frameworks, and operational excellence." },
            { id: "finance", name: "Finance", icon: "💰", system: "You are a financial analyst with comprehensive knowledge of financial modeling, valuation, and market analysis." },
            { id: "marketing", name: "Marketing", icon: "📱", system: "You are a marketing strategist with deep knowledge of brand development, customer acquisition, and campaign optimization." }
        ],
        "Creative": [
            { id: "writer", name: "Writer", icon: "✍️", system: "You are an expert writer skilled in narrative development, character creation, and compelling storytelling." },
            { id: "designer", name: "Designer", icon: "🎨", system: "You are a professional designer with expertise in visual communication, UX principles, and creative problem-solving." }
        ],
        "Science": [
            { id: "researcher", name: "Researcher", icon: "🔬", system: "You are a research scientist with expertise in experimental design, data analysis, and scientific communication." },
            { id: "medical", name: "Medical", icon: "⚕️", system: "You are a medical professional with comprehensive knowledge of human physiology and treatment approaches." }
        ]
    };
    
    // Populate roles by domain
    if (rolesContainer) {
        for (const [domain, roles] of Object.entries(expertRoles)) {
            // Create domain section
            const domainSection = document.createElement('div');
            domainSection.className = 'domain-section';
            domainSection.innerHTML = `<h4>${domain}</h4>`;
            rolesContainer.appendChild(domainSection);
            
            // Create role buttons
            roles.forEach(role => {
                const roleBtn = document.createElement('button');
                roleBtn.className = 'expert-role-button';
                roleBtn.dataset.role = role.id;
                roleBtn.innerHTML = `<span class="expert-role-icon">${role.icon}</span> ${role.name}`;
                
                roleBtn.addEventListener('click', function() {
                    // Update active state
                    if (activeRoleBtn) {
                        activeRoleBtn.classList.remove('active');
                    }
                    roleBtn.classList.add('active');
                    activeRoleBtn = roleBtn;
                    
                    // Update system prompt
                    if (systemPrompt) {
                        systemPrompt.value = role.system;
                    }
                    
                    // Update prompt on server
                    socket.emit('update_system_prompt', { prompt: role.system });
                    
                    // Add feedback message
                    const messageEvent = new CustomEvent('addSystemMessage', { 
                        detail: { message: `Switched to ${role.name} role` }
                    });
                    document.dispatchEvent(messageEvent);
                });
                
                rolesContainer.appendChild(roleBtn);
            });
        }
    }
    
    // Custom event listener for system messages
    document.addEventListener('addSystemMessage', function(e) {
        if (typeof addMessageToUI === 'function') {
            addMessageToUI('system', e.detail.message);
        }
    });
});
