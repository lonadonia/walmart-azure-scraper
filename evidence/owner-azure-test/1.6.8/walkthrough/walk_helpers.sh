bin () 
{ 
    find "$PKG/root/usr/bin" "$PKG/root/usr/sbin" "$PKG/root/usr/libexec" -maxdepth 3 -type f -perm -u+x -name "$1" 2> /dev/null | head -1
}
dk () 
{ 
    sudo -n env DOCKER_CONFIG="$D/cli" DOCKER_BUILDKIT=0 "$(bin docker)" -H "unix://$EXEC/docker.sock" "$@"
}
img () 
{ 
    echo "walmart-collector-q168d:$REL-$1"
}
url () 
{ 
    echo "postgresql://walmart_q167@$DBHOST:5432/$1"
}
psqlq () 
{ 
    psql -h "$DBHOST" -U walmart_q167 -d "$1" -Atc "$2"
}
cdbi () 
{ 
    local image=$1 vol=$2 db=$3;
    shift 4;
    dk run --rm --network host --read-only --tmpfs /tmp -v "$vol:/app/data" --env-file "$D/pg.env" -e "WALMART_COLLECTOR_DATABASE_URL=$(url "$db")" -e HTTP_PROXY=http://127.0.0.1:9 -e HTTPS_PROXY=http://127.0.0.1:9 -e NO_PROXY=127.0.0.1,localhost "$image" "$@"
}
cdb () 
{ 
    local e=$1 vol=$2 db=$3;
    shift 4;
    dk run --rm --network host --read-only --tmpfs /tmp -v "$vol:/app/data" --env-file "$D/pg.env" -e "WALMART_COLLECTOR_DATABASE_URL=$(url "$db")" -e HTTP_PROXY=http://127.0.0.1:9 -e HTTPS_PROXY=http://127.0.0.1:9 -e NO_PROXY=127.0.0.1,localhost "$(img "$e")" "$@"
}
replay_id () 
{ 
    psqlq "${2:-walmart_q168d_c_campaign}" "select id from runs where mode = 'REPLAY' and config_snapshot->'replay'->>'source_run' = '$1' order by created_at desc limit 1"
}
