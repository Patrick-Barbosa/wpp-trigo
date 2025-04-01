import streamlit as st
import pandas as pd
import requests
from time import sleep

def send_whatsapp_template(phone, name, token, number_id, template_name="welcome_message"):
    """Send WhatsApp template message with dynamic parameters"""
    url = f"https://graph.facebook.com/v22.0/{number_id}/messages"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    payload = {
        "messaging_product": "whatsapp",  # Note: Original had typo "messaging_product"
        "to": phone,
        "type": "template",
        "template": {
            "name": template_name,
            "language": {"code": "en_US"},  # Changed to Brazilian Portuguese
            "components": [{
                "type": "body"
#                "parameters": [{
#                    "type": "text",
#                    "text": name  # Using the name from Excel as parameter
#                }]
            }]
        }
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return True, None
    except requests.exceptions.HTTPError as err:
        return False, f"HTTP Error: {err}"
    except Exception as err:
        return False, f"Other Error: {err}"

def main():
    st.set_page_config(page_title=" Envios em massa - Trigo", page_icon="🌾")
    
    st.title("📲 Envio em Massa via WhatsApp")
    
    # Input Section
    with st.form("input_form"):
        uploaded_file = st.file_uploader("📂 Carregar arquivo Excel", type=["xlsx", "xls"])
        token = st.text_input("🔑 Token do WhatsApp", help="Token de acesso da API do WhatsApp")
        number_id = st.text_input("📱 WhatsApp Number ID", help="ID do número do WhatsApp Business")
        
        submit_btn = st.form_submit_button("🚀 Enviar Mensagens")

    if submit_btn:
        # Validation
        if not all([uploaded_file, token, number_id]):
            st.error("❌ Todos os campos são obrigatórios!")
            return

        try:
            df = pd.read_excel(uploaded_file)
            
            # Validate columns
            if not {'telefone', 'nome'}.issubset(df.columns):
                st.error("❌ O arquivo deve conter as colunas 'telefone' e 'nome'")
                return
            
            # Clean data
            df['telefone'] = df['telefone'].astype(str).str.strip()
            df['nome'] = df['nome'].astype(str).str.strip()

            total = len(df)
            success_count = 0
            progress_bar = st.progress(0)
            status_container = st.empty()

            for i, row in enumerate(df.itertuples(), 1):
                # Format phone number (remove non-numeric characters)
                phone = ''.join(filter(str.isdigit, row.telefone))
                
                # Add country code if missing (Brazil example)
                if not phone.startswith('55'):
                    phone = f'55{phone}'

                # Send message
                success, error = send_whatsapp_template(
                    phone=phone,
                    name=row.nome,
                    token=token,
                    number_id=number_id
                )

                # Update UI
                progress_bar.progress(i/total)
                status_text = f"""
                    📤 Enviando {i}/{total}
                    ✅ Sucessos: {success_count}
                    ❌ Falhas: {i - success_count - 1}
                """
                status_container.markdown(status_text)

                if success:
                    success_count += 1
                    st.success(f"✅ {row.nome} ({phone}) - Mensagem enviada!")
                else:
                    st.error(f"❌ {row.nome} ({phone}) - Erro: {error}")

                # Avoid rate limits
                sleep(1)

            # Final results
            st.balloons()
            st.success(f"""
                🎉 Processo concluído!
                Mensagens enviadas com sucesso: {success_count}/{total}
            """)

        except Exception as e:
            st.error(f"⛔ Erro crítico: {str(e)}")

if __name__ == "__main__":
    main()