class BirthdayAdmin {
    constructor() {
        this.apiBase = 'http://localhost:5000/api';
        this.init();
    }

    async init() {
        await this.loadBirthdays();
        this.setupEventListeners();
    }

    async loadBirthdays() {
        try {
            const response = await fetch(`${this.apiBase}/birthdays`);
            const birthdays = await response.json();
            this.renderBirthdays(birthdays);
        } catch (error) {
            console.error('Error loading birthdays:', error);
        }
    }

    renderBirthdays(birthdays) {
        const container = document.getElementById('birthdaysList');
        container.innerHTML = '';

        if (birthdays.length === 0) {
            container.innerHTML = '<p>Нет данных о днях рождения</p>';
            return;
        }

        birthdays.forEach(bday => {
            const item = document.createElement('div');
            item.className = 'birthday-item';
            item.innerHTML = `
                <div>
                    <strong>${bday.username}</strong> - 
                    ${new Date(bday.birth_date).toLocaleDateString('ru-RU')}
                </div>
                <button class="delete-btn" onclick="admin.deleteBirthday(${bday.id})">
                    Удалить
                </button>
            `;
            container.appendChild(item);
        });
    }

    async addBirthday(event) {
        event.preventDefault();
        
        const username = document.getElementById('username').value;
        const birthDate = document.getElementById('birthDate').value;

        if (!username || !birthDate) {
            alert('Заполните все поля');
            return;
        }

        try {
            const response = await fetch(`${this.apiBase}/birthdays`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    username: username.startsWith('@') ? username : '@' + username,
                    birth_date: birthDate
                })
            });

            if (response.ok) {
                document.getElementById('addForm').reset();
                await this.loadBirthdays();
            } else {
                alert('Ошибка при добавлении');
            }
        } catch (error) {
            console.error('Error adding birthday:', error);
        }
    }

    async deleteBirthday(id) {
        if (!confirm('Удалить эту запись?')) return;

        try {
            const response = await fetch(`${this.apiBase}/birthdays/${id}`, {
                method: 'DELETE'
            });

            if (response.ok) {
                await this.loadBirthdays();
            }
        } catch (error) {
            console.error('Error deleting birthday:', error);
        }
    }

    setupEventListeners() {
        document.getElementById('addForm').addEventListener('submit', (e) => this.addBirthday(e));
    }
}

// Инициализация админки
const admin = new BirthdayAdmin();