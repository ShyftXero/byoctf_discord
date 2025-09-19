FROM python:3.13.0rc1-bookworm

# Install build tools
RUN apt-get update && apt-get install -y pkg-config libssl-dev 

# Environmental configs
ENV BYOCTF="byoctf"
   
# Create a non-privileged user
RUN echo "[+] Creating user $BYOCTF" \
    && groupadd --system $BYOCTF \
    && useradd --create-home $BYOCTF -g $BYOCTF \ 
    && mkdir -p /home/$BYOCTF/.config \
    && chown -R $BYOCTF:$BYOCTF /home/$BYOCTF 
   
RUN mkdir -p /etc/apt/keyrings \
    && apt-get update -qq \
    && apt-get install -qq -y --no-install-recommends \
    apt-transport-https ca-certificates apt-utils gnupg2 unzip curl wget grep \
    vim iputils-ping dnsutils jq 

WORKDIR /app

# All installs can now be handled by uv pip install
COPY settings_template.py settings.py 
COPY custom_secrets_template.py custom_secrets.py
COPY . /app
RUN pip install uv
RUN uv pip install --system -r pyproject.toml
RUN uv pip install --system pycognito boto3 botocore dotenv
RUN python ./ctrl_ctf.py INIT
RUN python ./ctrl_ctf.py DEV_RESET
ENTRYPOINT ["/bin/bash"]
