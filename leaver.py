import requests
import json
import time
import datetime
import concurrent.futures
import os
import logging
from colorama import init, Fore, Style
from dataclasses import dataclass
from typing import Optional, List, Dict

init(autoreset=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('discord_leaver.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class UserProfile:
    id: str
    username: str
    discriminator: str
    display_name: str
    avatar: str
    created_at: datetime.datetime
    premium_type: int
    premium_since: Optional[datetime.datetime]
    verified: bool
    mfa_enabled: bool
    email: Optional[str]

CONFIG_FILE = "config.json"

def print_banner():
    banner = f"""
{Fore.CYAN}╔══════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                      ║
║     ██╗  ██╗ █████╗ ██╗██████╗  ██████╗                                             ║
║     ██║  ██║██╔══██╗██║██╔══██╗██╔═══██╗                                            ║
║     ███████║███████║██║██████╔╝██║   ██║                                            ║
║     ██╔══██║██╔══██║██║██╔══██╗██║   ██║                                            ║
║     ██║  ██║██║  ██║██║██║  ██║╚██████╔╝                                            ║
║     ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝╚═╝  ╚═╝ ╚═════╝                                             ║
║                                                                                      ║
║     {Fore.YELLOW}Vanityterrorist: Hairo{Fore.CYAN}                            ║
║                                                                                      ║
║     {Fore.GREEN}📞 Discord: stressource | discord.gg/mo{Fore.CYAN}                                      ║
║                                                                                      ║
║                                                                                      ║
╚══════════════════════════════════════════════════════════════════════════════════════╝
    """
    print(banner)

def save_config(token: str, webhook_url: str = ""):
    config = {
        "token": token,
        "webhook_url": webhook_url,
        "last_used": datetime.datetime.now().isoformat()
    }
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)

def load_config() -> dict:
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def send_webhook(webhook_url, content=None, embeds=None, file=None):
    try:
        if not webhook_url:
            return False
            
        data = {}
        files = {}
        
        if content:
            data["content"] = content
        if embeds:
            data["embeds"] = embeds
            
        if file:
            files = {
                'file': ('urls.txt', file, 'text/plain')
            }
            
        data["username"] = "Hairo"
        response = requests.post(webhook_url, data={"payload_json": json.dumps(data)}, files=files)
        
        if response.status_code == 200:
            logger.info("Webhook başarıyla gönderildi")
            return True
        else:
            logger.error(f"Webhook hatası: {response.status_code} - {response.text}")
            print(f"{Fore.RED}❌ Webhook hatası: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Webhook istek hatası: {str(e)}")
        print(f"{Fore.RED}❌ Webhook bağlantı hatası: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Webhook beklenmeyen hata: {str(e)}")
        print(f"{Fore.RED}❌ Webhook gönderilemedi: {str(e)}")
        return False

def validate_token(token) -> bool:
    headers = {
        "Authorization": token,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    }
    try:
        r = requests.get("https://discord.com/api/v9/users/@me", headers=headers, timeout=10)
        return r.status_code == 200
    except:
        return False

def get_user_profile(token) -> Optional[UserProfile]:
    headers = {
        "Authorization": token,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
        "X-Super-Properties": "eyJvcyI6IldpbmRvd3MiLCJicm93c2VyIjoiQ2hyb21lIiwiZGV2aWNlIjoiIiwic3lzdGVtX2xvY2FsZSI6InRyLVRSIiwiYnJvd3Nlcl91c2VyX2FnZW50IjoiTW96aWxsYS81LjAgKFdpbmRvd3MgTlQgMTAuMDsgV2luNjQ7IHg2NCkiLCJicm93c2VyX3ZlcnNpb24iOiIxMTYuMC4wLjAiLCJvc192ZXJzaW9uIjoiMTAiLCJyZWZlcnJlciI6IiIsInJlZmVycmluZ19kb21haW4iOiIiLCJyZWZlcnJlcl9jdXJyZW50IjoiIiwicmVmZXJyaW5nX2RvbWFpbl9jdXJyZW50IjoiIiwicmVsZWFzZV9jaGFubmVsIjoic3RhYmxlIiwiY2xpZW50X2J1aWxkX251bWJlciI6MjI3NDEzLCJjbGllbnRfZXZlbnRfc291cmNlIjpudWxsfQ=="
    }
    try:
        r = requests.get("https://discord.com/api/v9/users/@me", headers=headers, timeout=10)
        
        if r.status_code == 200:
            data = r.json()
            logger.info(f"Kullanıcı profili alındı: {data.get('username', 'Bilinmiyor')}")
            
            user_id = int(data['id'])
            discord_epoch = 1420070400000
            timestamp = ((user_id >> 22) + discord_epoch) / 1000
            created_at = datetime.datetime.fromtimestamp(timestamp)
            
            premium_since = None
            if data.get('premium_since'):
                try:
                    premium_since = datetime.datetime.fromisoformat(data['premium_since'].replace('Z', '+00:00'))
                except ValueError:
                    logger.warning("Premium since tarihi parse edilemedi")
            
            return UserProfile(
                id=data['id'],
                username=data['username'],
                discriminator=data.get('discriminator', '0'),
                display_name=data.get('display_name', data['username']),
                avatar=data.get('avatar', ''),
                created_at=created_at,
                premium_type=data.get('premium_type', 0),
                premium_since=premium_since,
                verified=data.get('verified', False),
                mfa_enabled=data.get('mfa_enabled', False),
                email=data.get('email')
            )
        elif r.status_code == 401:
            logger.error("Token geçersiz")
            print(f"{Fore.RED}❌ Token geçersiz!")
            return None
        elif r.status_code == 429:
            logger.warning("Rate limit aşıldı")
            print(f"{Fore.YELLOW}⚠️  Rate limit aşıldı, lütfen bekleyin...")
            return None
        else:
            logger.error(f"API hatası: {r.status_code} - {r.text}")
            print(f"{Fore.RED}❌ API hatası: {r.status_code}")
            return None
            
    except requests.exceptions.Timeout:
        logger.error("İstek zaman aşımına uğradı")
        print(f"{Fore.RED}❌ İstek zaman aşımına uğradı!")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"İstek hatası: {str(e)}")
        print(f"{Fore.RED}❌ Bağlantı hatası: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Beklenmeyen hata: {str(e)}")
        print(f"{Fore.RED}❌ Profil bilgisi alınamadı: {str(e)}")
        return None

def get_guilds(token):
    headers = {
        "Authorization": token,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
        "X-Super-Properties": "eyJvcyI6IldpbmRvd3MiLCJicm93c2VyIjoiQ2hyb21lIiwiZGV2aWNlIjoiIiwic3lzdGVtX2xvY2FsZSI6InRyLVRSIiwiYnJvd3Nlcl91c2VyX2FnZW50IjoiTW96aWxsYS81LjAgKFdpbmRvd3MgTlQgMTAuMDsgV2luNjQ7IHg2NCkiLCJicm93c2VyX3ZlcnNpb24iOiIxMTYuMC4wLjAiLCJvc192ZXJzaW9uIjoiMTAiLCJyZWZlcnJlciI6IiIsInJlZmVycmluZ19kb21haW4iOiIiLCJyZWZlcnJlcl9jdXJyZW50IjoiIiwicmVmZXJyaW5nX2RvbWFpbl9jdXJyZW50IjoiIiwicmVsZWFzZV9jaGFubmVsIjoic3RhYmxlIiwiY2xpZW50X2J1aWxkX251bWJlciI6MjI3NDEzLCJjbGllbnRfZXZlbnRfc291cmNlIjpudWxsfQ=="
    }
    try:
        r = requests.get("https://discord.com/api/v9/users/@me/guilds", headers=headers)
        if r.status_code == 200:
            return r.json()
        else:
            print(f"{Fore.RED}Hata: {r.status_code} - {r.text}")
            return None
    except Exception as e:
        print(f"{Fore.RED}Hata oluştu: {str(e)}")
        return None

def check_vanity(token, guild):
    headers = {
        "Authorization": token,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
        "X-Super-Properties": "eyJvcyI6IldpbmRvd3MiLCJicm93c2VyIjoiQ2hyb21lIiwiZGV2aWNlIjoiIiwic3lzdGVtX2xvY2FsZSI6InRyLVRSIiwiYnJvd3Nlcl91c2VyX2FnZW50IjoiTW96aWxsYS81LjAgKFdpbmRvd3MgTlQgMTAuMDsgV2luNjQ7IHg2NCkiLCJicm93c2VyX3ZlcnNpb24iOiIxMTYuMC4wLjAiLCJvc192ZXJzaW9uIjoiMTAiLCJyZWZlcnJlciI6IiIsInJlZmVycmluZ19kb21haW4iOiIiLCJyZWZlcnJlcl9jdXJyZW50IjoiIiwicmVmZXJyaW5nX2RvbWFpbl9jdXJyZW50IjoiIiwicmVsZWFzZV9jaGFubmVsIjoic3RhYmxlIiwiY2xpZW50X2J1aWxkX251bWJlciI6MjI3NDEzLCJjbGllbnRfZXZlbnRfc291cmNlIjpudWxsfQ=="
    }
    try:
        r = requests.get(f"https://discord.com/api/v9/guilds/{guild['id']}", headers=headers)
        if r.status_code == 200:
            guild_data = r.json()
            if guild_data.get('vanity_url_code'):
                return {
                    'id': guild['id'],
                    'name': guild['name'],
                    'vanity': guild_data['vanity_url_code'],
                    'member_count': guild_data.get('approximate_member_count', guild_data.get('member_count', 0)),
                    'owner': guild.get('owner', False)
                }
    except:
        pass
    return None

def leave_guild(token, guild_id):
    headers = {
        "Authorization": token,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    }
    r = requests.delete(f"https://discord.com/api/v9/users/@me/guilds/{guild_id}", headers=headers)
    return r.status_code == 204




def display_user_profile(profile: UserProfile):
    
    if not profile:
        return
    nitro_types = {
        0: "❌ Nitro Yok",
        1: "💎 Nitro Classic",
        2: "🌟 Nitro",
        3: "⭐ Nitro Basic"
    }
    
    nitro_status = nitro_types.get(profile.premium_type, "❓ Bilinmiyor")
    account_age = datetime.datetime.now() - profile.created_at
    days = account_age.days
    years = days // 365
    remaining_days = days % 365
    
    age_text = f"{years} yıl, {remaining_days} gün" if years > 0 else f"{days} gün"
    nitro_duration = ""
    if profile.premium_since:
        nitro_age = datetime.datetime.now() - profile.premium_since.replace(tzinfo=None)
        nitro_days = nitro_age.days
        nitro_years = nitro_days // 365
        nitro_remaining = nitro_days % 365
        nitro_duration = f" | Nitro Süresi: {nitro_years} yıl, {nitro_remaining} gün" if nitro_years > 0 else f" | Nitro Süresi: {nitro_days} gün"
    
    profile_info = f"""
{Fore.CYAN}╔══════════════════════════════════════════════════════════════════════════════════════╗
║                                {Fore.YELLOW}👤 KULLANICI PROFİLİ{Fore.CYAN}                                      ║
╠══════════════════════════════════════════════════════════════════════════════════════╣
║                                                                                      ║
║  {Fore.GREEN}👤 Kullanıcı Adı:{Fore.WHITE} {profile.username}#{profile.discriminator if profile.discriminator != '0' else ''}
║  {Fore.GREEN}🆔 Kullanıcı ID:{Fore.WHITE} {profile.id}
║  {Fore.GREEN}📝 Görünen Ad:{Fore.WHITE} {profile.display_name}
║  {Fore.GREEN}📅 Hesap Oluşturma:{Fore.WHITE} {profile.created_at.strftime('%d.%m.%Y %H:%M')}
║  {Fore.GREEN}⏰ Hesap Yaşı:{Fore.WHITE} {age_text}
║  {Fore.GREEN}💎 Nitro Durumu:{Fore.WHITE} {nitro_status}{nitro_duration}
║  {Fore.GREEN}✅ Doğrulanmış:{Fore.WHITE} {'✅ Evet' if profile.verified else '❌ Hayır'}
║  {Fore.GREEN}🔐 2FA Aktif:{Fore.WHITE} {'✅ Evet' if profile.mfa_enabled else '❌ Hayır'}
║                                                                                      ║
╚══════════════════════════════════════════════════════════════════════════════════════╝{Fore.RESET}
    """
    print(profile_info)

def show_menu():
    menu = f"""
{Fore.CYAN}╔══════════════════════════════════════════════════════════════════════════════════════╗
║                                {Fore.YELLOW}📋 ANA MENÜ{Fore.CYAN}                                             ║
╠══════════════════════════════════════════════════════════════════════════════════════╣
║                                                                                      ║
║  {Fore.GREEN}1.{Fore.WHITE} 🔍 Sunucu Bilgilerini Görüntüle ve İstatistikleri Gönder              ║
║  {Fore.GREEN}2.{Fore.WHITE} 🚪 Sunucudan Çık (ID veya Vanity URL ile)                             ║
║  {Fore.GREEN}3.{Fore.WHITE} 🔄 Token ve Webhook Bilgilerini Değiştir                              ║
║  {Fore.GREEN}4.{Fore.WHITE} 👤 Profil Bilgilerini Görüntüle                                       ║
║  {Fore.GREEN}q.{Fore.WHITE} ❌ Çıkış                                                               ║
║                                                                                      ║
╚══════════════════════════════════════════════════════════════════════════════════════╝{Fore.RESET}
    """
    print(menu)

def process_leave_command(input_text, guilds, vanity_guilds, token, webhook_url):
    input_text = input_text.strip()
    if input_text.isdigit():
        print(f"{Fore.YELLOW}ID ile aranıyor: {input_text}")
        target_guild = next((g for g in guilds if str(g['id']) == input_text), None)
    else:
        if input_text.startswith("id:"):
            input_text = input_text[3:].strip()
            print(f"{Fore.YELLOW}ID ile aranıyor: {input_text}")
            target_guild = next((g for g in guilds if str(g['id']) == input_text), None)
        else:
            vanity = input_text.replace("discord.gg/", "").strip()
            target_guild = next((g for g in vanity_guilds if g['vanity'].lower() == vanity.lower()), None)

    if target_guild:
        confirm = input(f"{Fore.YELLOW}'{target_guild['name']}' sunucusundan çıkmak istediğinize emin misiniz? (e/h): ").lower()
        if confirm == 'e':
            if leave_guild(token, target_guild['id']):
                print(f"{Fore.GREEN}✅ Sunucudan başarıyla çıkıldı: {target_guild['name']}")
                if webhook_url:
                    if 'vanity' in target_guild:
                        webhook_content = f"✅ Quit: discord.gg/{target_guild['vanity']} ({target_guild['name']})"
                    else:
                        webhook_content = f"✅ Quit: {target_guild['name']} [ID: {target_guild['id']}]"
                    send_webhook(webhook_url, content=webhook_content)
            else:
                print(f"{Fore.RED}❌ Sunucudan çıkılamadı!")
    else:
        print(f"{Fore.RED}❌ Bu vanity URL veya ID'ye sahip bir sunucu bulunamadı!")

def scan_servers(token, webhook_url):
    print(f"\n{Fore.YELLOW}⏳ Sunucular kontrol ediliyor...")
    guilds = get_guilds(token)
    if not guilds:
        print(f"{Fore.RED}❌ Token geçersiz veya sunucular alınamadı!")
        return None, None

    print(f"{Fore.CYAN}🔍 Toplam {len(guilds)} sunucu taranıyor...")

    vanity_guilds = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_to_guild = {executor.submit(check_vanity, token, guild): guild for guild in guilds}
        completed = 0
        for future in concurrent.futures.as_completed(future_to_guild):
            completed += 1
            print(f"\r{Fore.YELLOW}📊 İlerleme: {completed}/{len(guilds)} ({(completed/len(guilds)*100):.1f}%)", end="")
            result = future.result()
            if result:
                vanity_guilds.append(result)

    return guilds, vanity_guilds


def generate_server_report(guilds, vanity_guilds, profile, webhook_url):
    numeric_urls = []
    letter_urls = []
    mixed_urls = []
    no_vanity_guilds = []
    for guild in vanity_guilds:
        vanity = guild['vanity']
        member_count = f"{guild.get('member_count', 0):,}".replace(",", ".")
        owner_badge = " 👑" if guild.get('owner', False) else ""
        url_entry = f"discord.gg/{vanity} -> {member_count} üye [ID: {guild['id']}]{owner_badge}"
        
        if vanity.isdigit():
            numeric_urls.append(url_entry)
        elif vanity.isalpha():
            letter_urls.append(url_entry)
        else:
            mixed_urls.append(url_entry)
    vanity_guild_ids = set(guild['id'] for guild in vanity_guilds)
    for guild in guilds:
        if guild['id'] not in vanity_guild_ids:
            member_count = f"{guild.get('member_count', 0):,}".replace(",", ".")
            owner_badge = " 👑" if guild.get('owner', False) else ""
            no_vanity_guilds.append(f"{guild['name']} -> {member_count} üye [ID: {guild['id']}]{owner_badge}")
    urls_text = "═══════════════════ SUNUCU RAPORU ═══════════════════\n\n"
    
    if profile:
        nitro_types = {0: "❌", 1: "💎 Nitro Classic", 2: "🌟 Nitro", 3: "⭐ Nitro Basic"}
        nitro_status = nitro_types.get(profile.premium_type, "❓ Bilinmiyor")
        account_age = datetime.datetime.now() - profile.created_at
        age_text = f"{account_age.days // 365} yıl, {account_age.days % 365} gün"
        
        urls_text += f"👤 Kullanıcı: {profile.username}#{profile.discriminator if profile.discriminator != '0' else ''}\n"
        urls_text += f"🆔 ID: {profile.id}\n"
        urls_text += f"📅 Hesap Yaşı: {age_text}\n"
        urls_text += f"{nitro_status}\n"
        urls_text += f"Doğrulanmış: {'Evet' if profile.verified else 'Hayır'}\n\n"
    
    urls_text += "══════════════ SADECE SAYILAR ══════════════\n"
    urls_text += "\n".join(sorted(numeric_urls, key=lambda x: int("".join(filter(str.isdigit, x.split()[0])))))
    urls_text += "\n\n══════════════ SADECE HARFLER ══════════════\n"
    urls_text += "\n".join(sorted(letter_urls))
    urls_text += "\n\n══════════════ KARIŞIK URL'LER ══════════════\n"
    urls_text += "\n".join(sorted(mixed_urls))
    urls_text += "\n\n══════════════ URL'SİZ SUNUCULAR ══════════════\n"
    urls_text += "\n".join(sorted(no_vanity_guilds))
    urls_text += f"\n\n═══════════════ İSTATİSTİKLER ═══════════════\n"
    urls_text += f"📊 Toplam Sunucu: {len(guilds)}\n"
    urls_text += f"🔗 Vanity URL'li Sunucu: {len(vanity_guilds)}\n"
    urls_text += f"📝 URL'siz Sunucu: {len(no_vanity_guilds)}\n"
    urls_text += f"🔢 Sayı URL: {len(numeric_urls)}\n"
    urls_text += f"🔤 Harf URL: {len(letter_urls)}\n"
    urls_text += f"🔀 Karışık URL: {len(mixed_urls)}\n"
    urls_text += f"👑 Sahip Olduğu Sunucu: {len([g for g in guilds if g.get('owner', False)])}"
    
    if webhook_url:
        if profile:
            nitro_types = {0: "❌ Nitro Yok", 1: "💎 Nitro Classic", 2: "🌟 Nitro", 3: "⭐ Nitro Basic"}
            nitro_status = nitro_types.get(profile.premium_type, "❓ Bilinmiyor")
            
            profile_embed = {
                "title": "👤 Kullanıcı Profili",
                "description": f"**{profile.username}#{profile.discriminator if profile.discriminator != '0' else ''}**",
                                 "color": 0,
                "fields": [
                    {"name": "<:ID:1067590211581784105> ID", "value": profile.id, "inline": True},
                    {"name": "<:CAL:1067590204640198687> Hesap Oluşturma", "value": profile.created_at.strftime('%d.%m.%Y'), "inline": True},
                    {"name": "<:nitro:1412893297076076645>", "value": nitro_status, "inline": True},
                    {"name": "<a:wraithsdevTik:1295137598439690240> Doğrulanmış", "value": "Evet" if profile.verified else "Hayır", "inline": True},
                    {"name": "<:lock:1409317455050047631> 2FA", "value": "Aktif" if profile.mfa_enabled else "Pasif", "inline": True}
                ],
                "timestamp": datetime.datetime.now(datetime.UTC).isoformat()
            }
            send_webhook(webhook_url, embeds=[profile_embed])
        server_embed = {
            "title": "Succes",
            "description": f"<a:l_:1390743862770925702> **{len(guilds)}** server verified \n<:ask:1359280881860084014> **{len(vanity_guilds)}** vanity URL ",
                         "color": 0,
            "fields": [
                {"name": "<:arabistan:1359280912121991300> Sayı URL", "value": len(numeric_urls), "inline": True},
                {"name": "<:arabistan:1359280912121991300> Harf URL", "value": len(letter_urls), "inline": True},
                {"name": "<:arabistan:1359280912121991300> Karışık URL", "value": len(mixed_urls), "inline": True},
                {"name": "<:arabistan:1359280912121991300> Sahip Olduğu", "value": len([g for g in guilds if g.get('owner', False)]), "inline": True},
                {"name": "<:arabistan:1359280912121991300> URL'siz", "value": len(no_vanity_guilds), "inline": True},
                {"name": "<:CAL:1067590204640198687> Tarih", "value": datetime.datetime.now().strftime('%d.%m.%Y %H:%M'), "inline": True}
            ],
            "timestamp": datetime.datetime.now(datetime.UTC).isoformat()
        }
        send_webhook(webhook_url, embeds=[server_embed])
        send_webhook(webhook_url, content="@everyone 👁️ **Hairo infected**", file=urls_text)
    
    print(f"\n\n{Fore.GREEN}✅ Webhook'a başarıyla gönderildi!")
    return urls_text

def main():
    print_banner()
    config = load_config()
    token = config.get('token', '')
    webhook_url = config.get('webhook_url', '')
    if not token:
        print(f"{Fore.CYAN}🔑 İlk kurulum - Discord Token'ınızı girin:")
        while True:
            token = input(f"{Fore.GREEN}Token: ").strip()
            if not token:
                print(f"{Fore.RED}❌ Token gereklidir!")
                continue
            
            print(f"{Fore.YELLOW}🔍 Token doğrulanıyor...")
            if validate_token(token):
                print(f"{Fore.GREEN}✅ Token geçerli!")
                break
            else:
                print(f"{Fore.RED}❌ Geçersiz token! Lütfen tekrar deneyin.")
                continue
    else:
        print(f"{Fore.GREEN}✅ Kayıtlı token bulundu! Son kullanım: {config.get('last_used', 'Bilinmiyor')}")
        use_saved = input(f"{Fore.YELLOW}Kayıtlı token'ı kullanmak ister misiniz? (e/h): ").lower()
        if use_saved != 'e':
            while True:
                token = input(f"{Fore.GREEN}Yeni Token: ").strip()
                if not token:
                    print(f"{Fore.RED}❌ Token gereklidir!")
                    continue
                
                print(f"{Fore.YELLOW}🔍 Token doğrulanıyor...")
                if validate_token(token):
                    print(f"{Fore.GREEN}✅ Token geçerli!")
                    break
                else:
                    print(f"{Fore.RED}❌ Geçersiz token! Lütfen tekrar deneyin.")
                    continue
    if not webhook_url:
        webhook_url = input(f"{Fore.GREEN}Webhook URL (isteğe bağlı): ").strip()
    else:
        print(f"{Fore.GREEN}✅ Kayıtlı webhook bulundu!")
        use_saved_webhook = input(f"{Fore.YELLOW}Kayıtlı webhook'ı kullanmak ister misiniz? (e/h): ").lower()
        if use_saved_webhook != 'e':
            webhook_url = input(f"{Fore.GREEN}Yeni Webhook URL (isteğe bağlı): ").strip()
    save_config(token, webhook_url)
    print(f"\n{Fore.YELLOW}👤 Kullanıcı profili alınıyor...")
    profile = get_user_profile(token)
    
    if profile:
        print(f"{Fore.GREEN}✅ Profil bilgileri başarıyla alındı!")
        display_user_profile(profile)
    else:
        print(f"{Fore.RED}❌ Profil bilgisi alınamadı!")
    guilds = None
    vanity_guilds = None
    
    while True:
        show_menu()
        choice = input(f"\n{Fore.GREEN}Seçiminizi yapın: ").strip().lower()
        
        if choice == '1':
            guilds, vanity_guilds = scan_servers(token, webhook_url)
            if guilds:
                generate_server_report(guilds, vanity_guilds, profile, webhook_url)
        
        elif choice == '2':
            if not guilds:
                print(f"{Fore.YELLOW}⚠️  Önce sunucu bilgilerini tarayın (Seçenek 1)")
                continue
            
            print(f"\n{Fore.YELLOW}🚪 Sunucudan çıkmak için:")
            print(f"{Fore.CYAN}• ID ile çıkmak için: id:123456789")
            print(f"{Fore.CYAN}• Vanity ile çıkmak için: abc veya discord.gg/abc")
            
            while True:
                choice_input = input(f"\n{Fore.GREEN}Sunucu URL/ID (ana menüye dönmek için 'back'): ").strip()
                if choice_input.lower() == 'back':
                    break
                process_leave_command(choice_input, guilds, vanity_guilds, token, webhook_url)
        
        elif choice == '3':
            print(f"\n{Fore.CYAN}🔄 Token ve Webhook Güncelleme")
            
            while True:
                new_token = input(f"{Fore.GREEN}Yeni Token: ").strip()
                if not new_token:
                    print(f"{Fore.RED}❌ Token gereklidir!")
                    continue
                
                print(f"{Fore.YELLOW}🔍 Token doğrulanıyor...")
                if validate_token(new_token):
                    print(f"{Fore.GREEN}✅ Token geçerli!")
                    token = new_token
                    break
                else:
                    print(f"{Fore.RED}❌ Geçersiz token! Lütfen tekrar deneyin.")
                    continue
            
            webhook_url = input(f"{Fore.GREEN}Yeni Webhook URL: ").strip()
            save_config(token, webhook_url)
            print(f"{Fore.GREEN}✅ Bilgiler güncellendi!")
            
            profile = get_user_profile(token)
            if profile:
                display_user_profile(profile)
        
        elif choice == '4':
            if profile:
                display_user_profile(profile)
            else:
                print(f"{Fore.RED}❌ Profil bilgisi mevcut değil!")
        
        elif choice == 'q':
            print(f"\n{Fore.CYAN}👋 Güle güle!")
            break
        
        else:
            print(f"{Fore.RED}❌ Geçersiz seçim!")

if __name__ == "__main__":
    try:
        logger.info("Program başlatıldı")
        main()
        logger.info("Program normal şekilde sonlandırıldı")
    except KeyboardInterrupt:
        logger.info("Program kullanıcı tarafından sonlandırıldı")
        print(f"\n{Fore.YELLOW}👋 Program sonlandırıldı.")
    except Exception as e:
        logger.error(f"Beklenmeyen hata: {str(e)}")
        print(f"\n{Fore.RED}❌ Kritik hata oluştu: {str(e)}")
        print(f"{Fore.YELLOW}📄 Detaylı hata bilgisi 'discord_leaver.log' dosyasında kaydedildi.")
        input(f"\n{Fore.GREEN}Çıkmak için Enter'a basın...")
