from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# Simulasi data user (username dan password) untuk keperluan contoh
# Ganti data ini dengan sistem autentikasi yang sesuai dalam implementasi nyata
users = {
    'user1': 'password1',
    'user2': 'password2',
    # Tambahkan data user lain jika diperlukan
}

# Halaman login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Autentikasi user
        if username in users and users[username] == password:
            # Jika autentikasi berhasil, arahkan ke halaman pengaturan pond id
            return redirect(url_for('settings'))
        else:
            # Jika autentikasi gagal, arahkan kembali ke halaman login
            return render_template('login.html', message='Username atau password salah.')

    return render_template('login.html')

# Halaman pengaturan pond id
@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if request.method == 'POST':
        pond_id = request.form['pond_id']

        # Simpan pond id dalam file .env
        with open('.env', 'a') as env_file:
            env_file.write(f'POND_ID={pond_id}')

        return redirect(url_for('login'))  # Setelah mengatur pond id, arahkan kembali ke halaman login

    return render_template('settings.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
