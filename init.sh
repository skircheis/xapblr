source .venv/bin/activate

if [ -n "${BLOG_URL+1}" ]; then 
    xapblr index $BLOG_URL && systemctl --user enable --now xapblr-hourly@$BLOG_URL &
fi

touch /home/xapblr/blogs.txt
while IFS= read -r blog_url; do
    xapblr index $blog_url && systemctl --user enable --now xapblr-hourly@$blog_url 
done < /home/xapblr/blogs.txt &

uwsgi --ini ./config/uwsgi/xapblr.ini -H ./.venv
