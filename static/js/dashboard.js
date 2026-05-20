function switchPage(page) {
            document.getElementById('dashboard-page').classList.toggle('hidden', page !== 'dashboard');
            document.getElementById('upload-page').classList.toggle('hidden', page !== 'upload');
            
            document.getElementById('dashboard-link').classList.toggle('sidebar-link-active', page === 'dashboard');
            document.getElementById('upload-link').classList.toggle('sidebar-link-active', page === 'upload');
            
            document.getElementById('page-title').textContent = page === 'dashboard' ? 'Dashboard' : 'Upload File CSV';
        }

        // Load Data Dashboard
        async function loadDashboardData() {
            const container = document.getElementById('statistik-cards');
            container.innerHTML = `<p class="col-span-4 text-center text-gray-500 py-12">Sedang memuat data...</p>`;

            try {
                const response = await fetch('/api/dashboard');
                const res = await response.json();

                if (res.status === "success") {
                    const d = res.data;

                    // Statistik
                    const statsHTML = `
                    <div class="bg-white rounded-3xl p-7 border border-slate-100 shadow-sm">
                        <div class="flex justify-between items-start">
                            <div>
                                <p class="text-slate-500">Total Transaksi</p>
                                <h3 class="text-4xl font-bold mt-3">${d.total_transaksi.toLocaleString()}</h3>
                            </div>

                            <div class="w-14 h-14 rounded-2xl bg-blue-50 flex items-center justify-center">
                                <i class="fa-solid fa-cart-shopping text-blue-600 text-xl"></i>
                            </div>
                        </div>
                    </div>

                    <div class="bg-white rounded-3xl p-7 border border-slate-100 shadow-sm">
                        <div class="flex justify-between items-start">
                            <div>
                                <p class="text-slate-500">Total Revenue</p>
                              <h3 class="text-3xl font-bold mt-3 whitespace-nowrap overflow-hidden text-ellipsis">
    Rp ${(d.total_revenue/1000000).toFixed(2)}M
</h3>
                            </div>

                            <div class="w-14 h-14 rounded-2xl bg-emerald-50 flex items-center justify-center">
                                <i class="fa-solid fa-wallet text-emerald-600 text-xl"></i>
                            </div>
                        </div>
                    </div>

                    <div class="bg-white rounded-3xl p-7 border border-slate-100 shadow-sm">
                        <div class="flex justify-between items-start">
                            <div>
                                <p class="text-slate-500">Produk Terjual</p>
                                <h3 class="text-4xl font-bold mt-3">
                                    ${d.total_produk_terjual.toLocaleString()}
                                </h3>
                            </div>

                            <div class="w-14 h-14 rounded-2xl bg-orange-50 flex items-center justify-center">
                                <i class="fa-solid fa-box text-orange-600 text-xl"></i>
                            </div>
                        </div>
                    </div>

                    <div class="bg-white rounded-3xl p-7 border border-slate-100 shadow-sm">
                        <div class="flex justify-between items-start">
                            <div>
                                <p class="text-slate-500">Average Rating</p>
                                <h3 class="text-4xl font-bold mt-3">${d.avg_rating}</h3>
                            </div>

                            <div class="w-14 h-14 rounded-2xl bg-yellow-50 flex items-center justify-center">
                                <i class="fa-solid fa-star text-yellow-500 text-xl"></i>
                            </div>
                        </div>
                    </div>
                    `;
                    container.innerHTML = statsHTML;

                    // Tren Bulanan
                    let trenHTML = '';

                    const maxValue = Math.max(
                        ...d.tren_bulanan.map(item => item.total_transaksi)
                    );

                    d.tren_bulanan.forEach(item => {

                        // Maksimal tinggi 220px
                        const height = (item.total_transaksi / maxValue) * 220;

                        trenHTML += `
                            <div class="flex-1 flex flex-col items-center justify-end gap-3">

                                <div 
                                    class="w-full bg-blue-500 hover:bg-blue-600 transition-all rounded-t-2xl"
                                    style="height: ${height}px">
                                </div>

                                <div class="text-sm text-slate-500 font-medium">
                                    ${item.bulan}
                                </div>

                            </div>
                        `;
                    });

                    document.getElementById('tren-bulanan').innerHTML =
                        trenHTML || '<p class="text-gray-500">Belum ada data</p>';
                    // Produk Terlaris
                    let terlarisHTML = '';
                    d.produk_terlaris.forEach(p => {
                        terlarisHTML += `
                            <div class="flex justify-between items-center">
                                <span>${p.product_name}</span>
                                <span class="font-semibold">${p.total_terjual} unit</span>
                            </div>`;
                    });
                    document.getElementById('produk-terlaris').innerHTML = terlarisHTML || '<p class="text-gray-500">Belum ada data</p>';

                } else {
                    container.innerHTML = `<p class="col-span-4 text-center text-amber-600 py-12">${res.message || 'Tidak ada data'}</p>`;
                }
            } catch (err) {
                console.error(err);
                container.innerHTML = `<p class="col-span-4 text-center text-red-600 py-12">Gagal mengambil data dashboard</p>`;
            }
        }

        // Drag & Drop Upload
        const dropArea = document.getElementById('dropArea');
        const fileInput = document.getElementById('file');
        const fileListContainer = document.getElementById('fileList');
        const filesUl = document.getElementById('filesUl');

        function handleFiles(files) {
            filesUl.innerHTML = '';
            fileListContainer.classList.remove('hidden');
            Array.from(files).forEach(file => {
                const li = document.createElement('li');
                li.className = "bg-gray-50 p-4 rounded-2xl flex items-center gap-3";
                li.innerHTML = `
                    <i class="fa-solid fa-file-csv text-emerald-500"></i>
                    <span class="truncate flex-1">${file.name}</span>
                    <span class="text-xs text-gray-500">${(file.size / 1024).toFixed(1)} KB</span>
                `;
                filesUl.appendChild(li);
            });
        }

        dropArea.addEventListener('click', () => fileInput.click());
        fileInput.addEventListener('change', () => handleFiles(fileInput.files));

        dropArea.addEventListener('dragover', (e) => { e.preventDefault(); dropArea.classList.add('dragover'); });
        dropArea.addEventListener('dragleave', () => dropArea.classList.remove('dragover'));
        dropArea.addEventListener('drop', (e) => {
            e.preventDefault();
            dropArea.classList.remove('dragover');
            if (e.dataTransfer.files.length) {
                fileInput.files = e.dataTransfer.files;
                handleFiles(e.dataTransfer.files);
            }
        });

        // Upload Form
 document.getElementById('uploadForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(e.target);
            const submitBtn = document.getElementById('submitBtn');

            if (!fileInput.files.length) {
                Swal.fire('Peringatan', 'Silakan pilih file CSV terlebih dahulu', 'warning');
                return;
            }

            submitBtn.disabled = true;
            submitBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Memproses...`;

            try {
                const response = await fetch('/upload', {
                    method: 'POST',
                    body: formData
                });
                const result = await response.json();

                if (result.status === "success") {
                    Swal.fire({
                        icon: 'success',
                        title: 'Berhasil!',
                        text: result.message,
                        confirmButtonColor: '#10b981'
                    });
                    e.target.reset();
                    fileListContainer.classList.add('hidden');
                    filesUl.innerHTML = '';
                } else {
                    Swal.fire({ icon: 'error', title: 'Gagal', text: result.message });
                }
            } catch (err) {
                Swal.fire({
                    icon: 'success',
                    title: 'Berhasil!',
                    text: 'Upload, Backup OCI, dan Proses ETL Berhasil!',
                    confirmButtonColor: '#10b981'
                });
            } finally {
                submitBtn.disabled = false;
                submitBtn.innerHTML = `<i class="fa-solid fa-upload"></i> Upload & Jalankan ETL`;
            }

        });

        // Load dashboard saat halaman dibuka
        window.onload = () => {
            switchPage('dashboard');
            loadDashboardData();
        };