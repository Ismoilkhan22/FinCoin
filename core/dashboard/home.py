from contextlib import closing

from django.conf import settings
from django.core.paginator import Paginator
from django.db import connection
from django.shortcuts import render, redirect
from methodism import custom_response, dictfetchone, dictfetchall
from methodism.sqlpaginator import SqlPaginator

from base.custom import permission_checker, admin_permission_checker
from base.helper import cusmot_dictfetchall, custom_dictfetchone
from core.forms.auto import AlgorithmForm, CategoryForm
from core.models import New, Algorithm, Category


@admin_permission_checker
def home_page(request):
    balance = f"""
        select SUM(balance) as summ from core_card  
        where user_id = {request.user.id}
    """
    rating = f"""
            SELECT cast(COALESCE(SUM(card.balance), 0) as int) as balance, uu.id, COALESCE(uu.username, 'not set yet') as username,
             uu.phone, (COALESCE(uu.first_name, '') || ' ' || COALESCE(uu.last_name, '')) as full_name, uu.avatar, uu.level
            from core_user uu
            left join core_card card on card.user_id = uu.id
            group by uu.id, uu.username, uu.phone, uu.first_name, uu.last_name, uu.avatar
            order by balance desc 
            limit 5
    """
    news = "select id, img, title from core_new order by id desc limit 3"

    with closing(connection.cursor()) as cursor:
        cursor.execute(balance)
        balance = dictfetchone(cursor)

        cursor.execute(rating)
        rating = dictfetchall(cursor)

        cursor.execute(news)
        news = dictfetchall(cursor)

    return render(request, 'pages/index.html', context={
        "balance": balance['summ'],
        "rating": rating,
        "news": news
    })


@admin_permission_checker
def category(request, pk=None):
    pagination = Category.objects.all().order_by('-pk')
    paginator = Paginator(pagination, settings.PAGINATE_BY)
    page_number = request.GET.get("page", 1)
    paginated = paginator.get_page(page_number)
    ctx = {
        "roots": paginated,
        "pos": "list",
        'ctg_active': "active",
    }

    root = Category.objects.filter(pk=pk).first()
    form = CategoryForm(request.POST or None, instance=root or None)
    if form.is_valid():
        form.save()
        return redirect('category')
    ctx["form"] = form
    ctx['suggest_status'] = "form"

    return render(request, f'pages/ctg.html', ctx)


@admin_permission_checker
def algaritm(request, key=None, pk=None):
    if key == 'form':
        root = Algorithm.objects.filter(pk=pk).first()
        kwar = {
            'instance': root or None,
            'creator': request.user
        }
        form = AlgorithmForm(request.POST or None, **kwar)
        if form.is_valid():
            form.save()
            return redirect('all_algaritm')
        else:
            print(form.errors)
        return render(request, 'pages/algaritm.html', {'key': key, "form": form})

    all_algaritm = f""" select cor_al.id, cor_al.reward, cor_al.description, cor_al.bonus, (COALESCE(user_c.first_name, '') || ' ' || COALESCE(user_c.last_name, '')) as full_name
                from core_algorithm cor_al
                    left join core_user user_c on cor_al.creator_id == user_c.id
                """
    user = f"""
            select c_user.id, c_user.first_name, c_user.last_name from core_user c_user
            """
    bonuses = "select bonus from core_algorithm"

    with closing(connection.cursor()) as cursor:
        cursor.execute(all_algaritm)
        algarithm = dictfetchall(cursor)

        cursor.execute(user)
        user = dictfetchall(cursor)

        cursor.execute(bonuses)
        bonuses = cursor.fetchall()

    return render(request, 'pages/algaritm.html',
                  {"all_algorithm": algarithm, 'key': key, 'user': user, "bonuses": [x[0] for x in bonuses]})
