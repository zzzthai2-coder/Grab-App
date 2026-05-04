import gradio as gr
import folium
import urllib.request
import urllib.parse
import json
import math
import random
import os  # <-- THÊM DÒNG NÀY ĐỂ MÁY CHỦ ĐỌC ĐƯỢC CỔNG (PORT)

# ================= 1. HÀM TÍNH TIỀN CHUẨN =================
def tinh_tien_chuan(khoang_cach, loai_xe, thoi_tiet, giao_thong, ma_km):
    bang_gia = {
        "🏍️ GrabBike": {"mo_cua": 12500, "gia_km_tiep": 4300, "km_mo_cua": 2.0},
        "🚗 GrabCar 4 Chỗ": {"mo_cua": 29000, "gia_km_tiep": 10000, "km_mo_cua": 2.0},
        "🚙 GrabCar 7 Chỗ": {"mo_cua": 34000, "gia_km_tiep": 13000, "km_mo_cua": 2.0}
    }
    
    xe = bang_gia.get(loai_xe, bang_gia["🏍️ GrabBike"])
    
    if khoang_cach <= xe["km_mo_cua"]:
        tien_co_ban = xe["mo_cua"]
    else:
        km_vuot = khoang_cach - xe["km_mo_cua"]
        tien_co_ban = xe["mo_cua"] + (km_vuot * xe["gia_km_tiep"])
        
    he_so_phu_phi = 1.0
    if thoi_tiet == "🌧️ Mưa to": he_so_phu_phi += 0.2
    if giao_thong == "🚦 Kẹt xe": he_so_phu_phi += 0.3
    
    tien_sau_phu_phi = tien_co_ban * he_so_phu_phi
    phi_nen_tang = 2000 
    tong_tam_tinh = tien_sau_phu_phi + phi_nen_tang
    
    giam_gia = 0
    ma = ma_km.strip().upper()
    if ma == "GRAB50": 
        giam_gia = min(tong_tam_tinh * 0.5, 50000) 
    elif ma == "GIAM20K": 
        giam_gia = 20000
        
    tong_tien_cuoi = max(0, tong_tam_tinh - giam_gia)
    tong_tien_lam_tron = math.ceil(tong_tien_cuoi / 1000) * 1000
    
    return tong_tien_lam_tron, int(giam_gia), int(tien_co_ban), phi_nen_tang, he_so_phu_phi

# ================= 2. HÀM XỬ LÝ TỌA ĐỘ & BẢN ĐỒ =================
def lay_toa_do(dia_chi):
    if not dia_chi: return None
    if "việt nam" not in dia_chi.lower(): dia_chi += ", Việt Nam"
    try:
        url = f"https://nominatim.openstreetmap.org/search?q={urllib.parse.quote(dia_chi)}&format=json&limit=1"
        req = urllib.request.Request(url, headers={'User-Agent': 'MiniGrab/7.0'})
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            if data: return float(data[0]['lat']), float(data[0]['lon'])
    except: pass
    return None

def tinh_khoang_cach(p1, p2):
    R = 6371.0
    lat1, lon1 = math.radians(p1[0]), math.radians(p1[1])
    lat2, lon2 = math.radians(p2[0]), math.radians(p2[1])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    return round(R * (2 * math.atan2(math.sqrt(a), math.sqrt(1-a))), 1)

# ================= 3. LOGIC XỬ LÝ CHÍNH =================
def xu_ly_dat_xe(diem_don, diem_den, loai_xe, thoi_tiet, giao_thong, ma_km):
    if not diem_don or not diem_den:
        return "❌ Vui lòng nhập đủ địa chỉ!", "", gr.update(visible=False), ""

    p1, p2 = lay_toa_do(diem_don), lay_toa_do(diem_den)
    if not p1 or not p2:
        return "❌ Không tìm thấy địa điểm. Hãy thử nhập cụ thể hơn!", "", gr.update(visible=False), ""

    km = max(tinh_khoang_cach(p1, p2), 1.0)
    
    m = folium.Map(location=[(p1[0]+p2[0])/2, (p1[1]+p2[1])/2], zoom_start=13)
    folium.Marker(p1, tooltip="Điểm đón", icon=folium.Icon(color='green')).add_to(m)
    folium.Marker(p2, tooltip="Điểm đến", icon=folium.Icon(color='red')).add_to(m)
    folium.PolyLine([p1, p2], color="#00B14F", weight=5).add_to(m)

    tong, giam, co_ban, phi_app, he_so = tinh_tien_chuan(km, loai_xe, thoi_tiet, giao_thong, ma_km)

    bien_lai = f"""
    ### 🧾 CHI TIẾT CHUYẾN ĐI
    - **Quãng đường:** {km} km
    - **Giá cước cơ bản:** {co_ban:,}đ
    - **Phụ phí (Thời tiết/Giao thông):** +{int(co_ban*(he_so-1)):,}đ
    - **Phí nền tảng:** +{phi_app:,}đ
    - **Khuyến mãi:** -{giam:,}đ
    ---
    ## 💰 TỔNG CỘNG: <span style='color: #00B14F;'>{tong:,} VNĐ</span>
    """
    return bien_lai, m._repr_html_(), gr.update(visible=True), ""

def xac_nhan_don(loai_xe):
    danh_sach_tai_xe = ["Nguyễn Văn An", "Trần Minh Tâm", "Lê Quốc Bình", "Phạm Hải Đăng", "Vũ Hoàng Tuấn", "Đinh Hữu Đạt"]
    tai_xe_random = random.choice(danh_sach_tai_xe)
    
    if "Bike" in loai_xe:
        dong_xe = random.choice(["Honda Wave Alpha", "Yamaha Sirius", "Honda Vision", "Yamaha Exciter 150"])
    else:
        dong_xe = random.choice(["Toyota Vios", "Hyundai Accent", "Mitsubishi Xpander", "Kia Morning"])
        
    bien_so = f"{random.randint(11,99)}{random.choice('ABCDEFGH')}-{random.randint(100,999)}.{random.randint(10,99)}"
    thoi_gian_cho = random.randint(2, 8)
    
    html_success = f"""
    <div style="background-color: #E8F5E9; color: #000000; padding: 20px; border-radius: 12px; border: 2px solid #81C784; text-align: center; margin-top: 15px; font-family: sans-serif;">
        <h2 style="margin-top: 0; color: #1B5E20; font-weight: bold;">✅ ĐẶT XE THÀNH CÔNG!</h2>
        <p style="font-size: 16px; color: #000000; margin: 10px 0;">Tài xế đã nhận cuốc và đang di chuyển đến điểm đón.</p>
        <hr style="border: 0; border-top: 1px solid #A5D6A7; margin: 15px 0;">
        
        <h3 style="margin-bottom: 5px; color: #000000; font-weight: bold;">
            👨‍✈️ Tài xế: <span style="font-weight: bold; color: #000000;">{tai_xe_random}</span> ⭐️ 4.9
        </h3>
        
        <p style="font-size: 16px; margin: 8px 0; color: #000000;">
            🚗 Phương tiện: <span style="font-weight: bold; color: #000000;">{dong_xe}</span>
        </p>
        
        <p style="font-size: 16px; margin: 8px 0; color: #000000;">
            🪪 Biển số xe: <b style="background: #FFD54F; padding: 2px 8px; border-radius: 4px; border: 1px solid #333; color: #000000;">{bien_so}</b>
        </p>
        
        <h3 style="margin-top: 15px; color: #D32F2F; font-weight: bold;">⏱️ Vui lòng đợi trong: {thoi_gian_cho} phút</h3>
    </div>
    """
    return html_success, gr.update(visible=False)

# ================= 4. GIAO DIỆN GRADIO =================
with gr.Blocks(theme=gr.themes.Soft(primary_hue="green"), title="Mini Grab App") as demo:
    gr.Markdown("# <center style='color: #00B14F; font-weight: bold;'>🚕 MINI GRAB PRO</center>")
    
    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### 📍 Thông tin đặt xe")
            txt_don = gr.Textbox(label="Điểm đón", placeholder="VD: Landmark 81, TP.HCM")
            txt_den = gr.Textbox(label="Điểm đến", placeholder="VD: Sân bay Tân Sơn Nhất")
            
            rad_xe = gr.Radio(["🏍️ GrabBike", "🚗 GrabCar 4 Chỗ", "🚙 GrabCar 7 Chỗ"], label="Chọn loại xe", value="🏍️ GrabBike")
            
            with gr.Row():
                rad_tt = gr.Radio(["☀️ Bình thường", "🌧️ Mưa to"], label="Thời tiết", value="☀️ Bình thường")
                rad_gt = gr.Radio(["🟢 Thông thoáng", "🚦 Kẹt xe"], label="Giao thông", value="🟢 Thông thoáng")
            
            txt_ma = gr.Textbox(label="Mã giảm giá", placeholder="Nhập GRAB50 hoặc GIAM20K")
            btn_tinh = gr.Button("🔍 KIỂM TRA GIÁ & LỘ TRÌNH", variant="secondary")

        with gr.Column(scale=1):
            gr.Markdown("### 🗺️ Bản đồ & Thanh toán")
            html_map = gr.HTML()
            md_bill = gr.Markdown("*Vui lòng nhập điểm đón/đến và bấm Kiểm tra giá.*")
            
            with gr.Column(visible=False) as col_confirm:
                btn_book = gr.Button("🚀 XÁC NHẬN ĐẶT XE NGAY", variant="primary", size="lg")
            
            html_success = gr.HTML()

    # --- LIÊN KẾT SỰ KIỆN ---
    btn_tinh.click(
        fn=xu_ly_dat_xe, 
        inputs=[txt_don, txt_den, rad_xe, rad_tt, rad_gt, txt_ma], 
        outputs=[md_bill, html_map, col_confirm, html_success]
    )
    
    btn_book.click(
        fn=xac_nhan_don, 
        inputs=[rad_xe], 
        outputs=[html_success, col_confirm]
    )

# === ĐÃ SỬA PHẦN NÀY ĐỂ CHẠY TRÊN MÁY CHỦ RENDER ===
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    demo.launch(server_name="0.0.0.0", server_port=port)
